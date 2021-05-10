#pragma once

#include <hive/protocol/transaction.hpp>
#include <hive/protocol/optional_automated_actions.hpp>

#include <fc/int_array.hpp>
#include <fc/reflect/reflect.hpp>
#include <vector>

#define HIVE_NUM_RESOURCE_TYPES     5

namespace hive { namespace plugins { namespace rc {

enum rc_resource_types
{
  resource_history_bytes,
  resource_new_accounts,
  resource_market_bytes,
  resource_state_bytes,
  resource_execution_time
};

typedef fc::int_array< int64_t, HIVE_NUM_RESOURCE_TYPES > resource_count_type;

struct count_resources_result
{
  resource_count_type                            resource_count;
};

void count_resources(
  const hive::protocol::signed_transaction& tx,
  count_resources_result& result,
  const time_point_sec& head_block_time
  );

void count_resources(
  const hive::protocol::optional_automated_action&,
  count_resources_result& result,
  const time_point_sec& head_block_time
  );

} } } // hive::plugins::rc

FC_REFLECT_ENUM( hive::plugins::rc::rc_resource_types,
    (resource_history_bytes)
    (resource_new_accounts)
    (resource_market_bytes)
    (resource_state_bytes)
    (resource_execution_time)
  )

FC_REFLECT( hive::plugins::rc::count_resources_result,
  (resource_count)
)

FC_REFLECT_TYPENAME( hive::plugins::rc::resource_count_type )
