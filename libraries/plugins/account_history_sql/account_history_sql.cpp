#include <hive/plugins/account_history_sql/account_history_sql_plugin.hpp>

#include <hive/utilities/postgres_connection_holder.hpp>

namespace hive
{
 namespace plugins
 {
  namespace account_history_sql
  {
    using chain::database;
    using hive::utilities::postgres_connection_holder;
    using protocol::operation;

    namespace detail
    {
      class account_history_sql_plugin_impl
      {
        public:
          account_history_sql_plugin_impl(const std::string &url) : _db( appbase::app().get_plugin< hive::plugins::chain::chain_plugin >().db() ), connection{url}
          {}

          virtual ~account_history_sql_plugin_impl()
          {
            ilog("finishing account_history_sql_plugin_impl destructor...");
          }

          void get_ops_in_block( account_history_sql::account_history_sql_plugin::sql_result_type sql_result,
                                uint32_t block_num, bool only_virtual, const fc::optional<bool>& include_reversible );

          void get_transaction( hive::protocol::annotated_signed_transaction& sql_result,
                                const hive::protocol::transaction_id_type& id, const fc::optional<bool>& include_reversible );

          void get_account_history( account_history_sql::account_history_sql_plugin::sql_sequence_result_type sql_sequence_result,
                                    const hive::protocol::account_name_type& account, uint64_t start, uint32_t limit,
                                    const fc::optional<bool>& include_reversible,
                                    const fc::optional<uint64_t>& operation_filter_low,
                                    const fc::optional<uint64_t>& operation_filter_high );

          void enum_virtual_ops( account_history_sql::account_history_sql_plugin::sql_result_type sql_result,
                                uint32_t block_range_begin, uint32_t block_range_end,
                                const fc::optional<bool>& include_reversible,
                                const fc::optional<uint64_t>& operation_begin, const fc::optional< uint32_t >& limit,
                                const fc::optional<uint32_t>& filter );

        private:

          database &_db;

          postgres_connection_holder connection;

          void fill_object( const pqxx::row& row, account_history_sql_object& obj, fc::optional<uint32_t>block_num );
          void create_filter_array( const std::vector<uint32_t>& v, std::string& filter_array );
          void gather_operations_from_filter( const fc::optional<uint64_t>& filter, std::vector<uint32_t>& v, bool high );
          void gather_virtual_operations_from_filter( const fc::optional<uint32_t>& filter, std::vector<uint32_t>& v );

      };//class account_history_sql_plugin_impl

      void account_history_sql_plugin_impl::fill_object( const pqxx::row& row, account_history_sql_object& obj, fc::optional<uint32_t>block_num = fc::optional<uint32_t>() )
      {
          uint32_t cnt = 0;

          obj.trx_id        = hive::protocol::transaction_id_type( row[ cnt++ ].as< std::string >() );
          obj.block         = block_num.valid() ? ( *block_num ) : row[ cnt++ ].as< uint32_t >();

          obj.trx_in_block  = row[ cnt++ ].as< uint32_t >();

          obj.op_in_trx     = row[ cnt++ ].as< uint32_t >();
          obj.virtual_op    = static_cast< uint32_t >( row[ cnt++ ].as< bool >() );
          obj.timestamp     = fc::time_point_sec::from_iso_string( row[ cnt++ ].as< std::string >() );

          obj.op            = fc::json::from_string( row[ cnt++ ].as< std::string >() );

          //not used???
          obj.operation_id = row[ cnt++ ].as< uint64_t >();
      }

      void account_history_sql_plugin_impl::create_filter_array( const std::vector<uint32_t>& v, std::string& filter_array )
      {
        filter_array = "ARRAY[ ";
        bool _first = true;

        for( auto val : v )
        {
          filter_array += _first ? std::to_string( val ) : ( ", " + std::to_string( val ) );
          _first = false;
        }
        filter_array += " ]::INT[]";
      }

      void account_history_sql_plugin_impl::gather_operations_from_filter( const fc::optional<uint64_t>& filter, std::vector<uint32_t>& v, bool high )
      {
        if( !filter.valid() )
          return;

        uint64_t _val = *filter;
        for( uint64_t it = 0; it < 64; ++it )
        {
          if( _val & 1 )
            v.push_back( high ? ( it + 64 ) : it );
          _val >>= 1;
        }
      }

      void account_history_sql_plugin_impl::gather_virtual_operations_from_filter( const fc::optional<uint32_t>& filter, std::vector<uint32_t>& v )
      {
        if( !filter.valid() )
          return;

        uint64_t _val = *filter;
        for( uint64_t it = 0; it < 32; ++it )
        {
          if( _val & 1 )
            v.push_back( it );
          _val >>= 1;
        }
      }

      void account_history_sql_plugin_impl::get_ops_in_block( account_history_sql::account_history_sql_plugin::sql_result_type sql_result,
                                                        uint32_t block_num, bool only_virtual, const fc::optional<bool>& include_reversible )
      {
        const int NR_FIELDS = 7;

        pqxx::result result;
        std::string sql;

        if( only_virtual )
          sql = "select * from ah_get_ops_in_block( " + std::to_string( block_num ) + ", 2::SMALLINT ) order by _trx_in_block, _virtual_op;";
        else
          sql = "select * from ah_get_ops_in_block( " + std::to_string( block_num ) + ", 0::SMALLINT ) order by _trx_in_block, _virtual_op;";

        if( !connection.exec_single_in_transaction( sql, &result ) )
        {
          wlog( "Execution of query ${sql} failed", ("sql", sql) );
          return;
        }

        for( const auto& row : result )
        {
          account_history_sql_object ah_obj;

          FC_ASSERT( row.size() == NR_FIELDS, "The database returned ${db_size} fields, but there is required ${req_size} fields",
                                              ( "db_size", row.size() )( "req_size", NR_FIELDS ) );

          fill_object( row, ah_obj, block_num );

          sql_result( ah_obj );
        }
      }

      void account_history_sql_plugin_impl::get_transaction( hive::protocol::annotated_signed_transaction& sql_result,
                                                            const hive::protocol::transaction_id_type& id, const fc::optional<bool>& include_reversible )
      {
        const int TRX_NR_FIELDS = 6;
        const int OP_NR_FIELDS = 2;

        pqxx::result result;
        std::string sql;

        sql = "select * from ah_get_trx( '"+ id.str() + "' )";

        if( !connection.exec_single_in_transaction( sql, &result ) )
        {
          wlog( "Execution of query ${sql} failed", ("sql", sql) );
          return;
        }

        FC_ASSERT( result.size() == 1 , "The database returned ${db_size} records, but there is required only 1 record",
                                        ( "db_size", result.size() ) );

        const auto& row = result[0];
        FC_ASSERT( row.size() >= TRX_NR_FIELDS, "The database returned ${db_size} fields, but there is required ${req_size} fields",
                                                ( "db_size", row.size() )( "req_size", TRX_NR_FIELDS ) );

        uint32_t cnt = 0;

        sql_result.ref_block_num    = row[ cnt++ ].as< uint32_t >();
        sql_result.ref_block_prefix = row[ cnt++ ].as< uint32_t >();
        sql_result.expiration       = fc::time_point_sec::from_iso_string( row[ cnt++ ].as< std::string >() );
        sql_result.block_num        = row[ cnt++ ].as< uint32_t >();
        sql_result.transaction_num  = row[ cnt++ ].as< uint32_t >();
        uint32_t trx_in_block       = row[ cnt++ ].as< uint32_t >();

        sql_result.transaction_id   = id;

        sql = "select * from ah_get_ops_in_trx( " + std::to_string( sql_result.block_num ) + ", " + std::to_string( trx_in_block ) + " )";

        if( !connection.exec_single_in_transaction( sql, &result ) )
        {
          wlog( "Execution of query ${sql} failed", ("sql", sql) );
          return;
        }

        for( const auto& row : result )
        {
          FC_ASSERT( row.size() >= OP_NR_FIELDS, "The database returned ${db_size} fields, but there is required ${req_size} fields", ( "db_size", row.size() )( "req_size", OP_NR_FIELDS ) );

          uint32_t cnt = 0;

          account_history_sql_object temp;
          temp.op   = fc::json::from_string( row[ cnt++ ].as< std::string >() );

          sql_result.operations.emplace_back( std::move( temp.get_op() ) );
        }
      }

      void account_history_sql_plugin_impl::get_account_history( account_history_sql::account_history_sql_plugin::sql_sequence_result_type sql_sequence_result,
                                                            const hive::protocol::account_name_type& account, uint64_t start, uint32_t limit,
                                                            const fc::optional<bool>& include_reversible,
                                                            const fc::optional<uint64_t>& operation_filter_low,
                                                            const fc::optional<uint64_t>& operation_filter_high )
      {
        std::vector<uint32_t> v;
        gather_operations_from_filter( operation_filter_low, v, false/*high*/ );
        gather_operations_from_filter( operation_filter_high, v, true/*high*/ );

        std::string filter_array;
        create_filter_array( v, filter_array );

        const int NR_FIELDS = 9;

        pqxx::result result;
        std::string sql;

        sql = "select * from ah_get_account_history(" + filter_array + ", '" + account + "', " + std::to_string( start ) + ", " + std::to_string( limit ) +" )";

        if( !connection.exec_single_in_transaction( sql, &result ) )
        {
          wlog( "Execution of query ${sql} failed", ("sql", sql) );
          return;
        }

        uint32_t cnt = start - limit + 1;
        for( const auto& row : result )
        {
          account_history_sql_object ah_obj;

          FC_ASSERT( row.size() >= NR_FIELDS, "The database returned ${db_size} fields, but there is required ${req_size} fields", ( "db_size", row.size() )( "req_size", NR_FIELDS ) );

          fill_object( row, ah_obj );

          sql_sequence_result( cnt++, ah_obj );
        }
      }

      void account_history_sql_plugin_impl::enum_virtual_ops( account_history_sql::account_history_sql_plugin::sql_result_type sql_result,
                                                        uint32_t block_range_begin, uint32_t block_range_end,
                                                        const fc::optional<bool>& include_reversible,
                                                        const fc::optional< uint64_t >& operation_begin, const fc::optional< uint32_t >& limit,
                                                        const fc::optional< uint32_t >& filter )
      {
        const int NR_FIELDS = 9;
        const int DEFAULT_LIMIT = 1000;

        pqxx::result result;
        std::string sql;

        std::vector<uint32_t> v;
        gather_virtual_operations_from_filter( filter, v );

        std::string filter_array;
        create_filter_array( v, filter_array );

        sql = "select * from ah_get_enum_virtual_ops( "
                + filter_array + ", "
                + std::to_string( block_range_begin ) + ", "
                + std::to_string( block_range_end ) + ", "
                + std::to_string( operation_begin.valid() ? *operation_begin : 0 ) + ", "
                + std::to_string( limit.valid() ? *limit : DEFAULT_LIMIT ) + " )";

        if( !connection.exec_single_in_transaction( sql, &result ) )
        {
          wlog( "Execution of query ${sql} failed", ("sql", sql) );
          return;
        }

        for( const auto& row : result )
        {
          account_history_sql_object ah_obj;

          FC_ASSERT( row.size() >= NR_FIELDS, "The database returned ${db_size} fields, but there is required ${req_size} fields",
                                              ( "db_size", row.size() )( "req_size", NR_FIELDS ) );

          fill_object( row, ah_obj );

          sql_result( ah_obj );
        }
      }

    }//namespace detail
  

    account_history_sql_plugin::account_history_sql_plugin() {}
    account_history_sql_plugin::~account_history_sql_plugin() {}

    void account_history_sql_plugin::set_program_options(options_description &cli, options_description &cfg)
    {
      //ahsql-url = dbname=ah_db_name user=postgres password=pass hostaddr=127.0.0.1 port=5432
      cfg.add_options()("ahsql-url", boost::program_options::value<string>(), "postgres connection string for AH database");
    }

    void account_history_sql_plugin::plugin_initialize(const boost::program_options::variables_map &options)
    {
      ilog("Initializing SQL account history plugin");
      FC_ASSERT(options.count("ahsql-url"), "`ahsql-url` is required");
      my = std::make_unique<detail::account_history_sql_plugin_impl>(options["ahsql-url"].as<fc::string>());
    }

    void account_history_sql_plugin::plugin_startup()
    {
      ilog("sql::plugin_startup()");
    }

    void account_history_sql_plugin::plugin_shutdown()
    {
      ilog("sql::plugin_shutdown()");
    }

    void account_history_sql_plugin::get_ops_in_block( sql_result_type sql_result,
                                                      uint32_t block_num, bool only_virtual, const fc::optional<bool>& include_reversible ) const
    {
      my->get_ops_in_block( sql_result, block_num, only_virtual, include_reversible );
    }

    void account_history_sql_plugin::get_transaction( hive::protocol::annotated_signed_transaction& sql_result,
                                                      const hive::protocol::transaction_id_type& id, const fc::optional<bool>& include_reversible ) const
    {
      my->get_transaction( sql_result, id, include_reversible );
    }

    void account_history_sql_plugin::get_account_history( sql_sequence_result_type sql_sequence_result,
                                                          const hive::protocol::account_name_type& account, uint64_t start, uint32_t limit,
                                                          const fc::optional<bool>& include_reversible,
                                                          const fc::optional<uint64_t>& operation_filter_low,
                                                          const fc::optional<uint64_t>& operation_filter_high ) const
    {
      my->get_account_history( sql_sequence_result, account, start, limit, include_reversible, operation_filter_low, operation_filter_high );
    }

    void account_history_sql_plugin::enum_virtual_ops( sql_result_type sql_result,
                                                      uint32_t block_range_begin, uint32_t block_range_end,
                                                      const fc::optional<bool>& include_reversible,
                                                      const fc::optional< uint64_t >& operation_begin, const fc::optional< uint32_t >& limit,
                                                      const fc::optional< uint32_t >& filter ) const
    {
      my->enum_virtual_ops( sql_result, block_range_begin, block_range_end, include_reversible,
                            operation_begin, limit, filter );
    }

  } // namespace account_history_sql
 }  // namespace plugins
} // namespace hive
