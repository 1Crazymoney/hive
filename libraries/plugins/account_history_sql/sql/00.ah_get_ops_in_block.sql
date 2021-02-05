DROP FUNCTION IF EXISTS ah_get_ops_in_block;
CREATE FUNCTION ah_get_ops_in_block( in _BLOCK_NUM INT, in _OP_TYPE SMALLINT )
RETURNS TABLE(
    _trx_id TEXT,
    _trx_in_block BIGINT,
    _op_in_trx INT,
    _virtual_op BOOLEAN,
    _timestamp TEXT,
    _value TEXT,
    _operation_id INT
)
AS
$function$
BEGIN

 RETURN QUERY
  SELECT
  (
    CASE
    WHEN ht.trx_hash IS NULL THEN '0000000000000000000000000000000000000000'
    ELSE encode( ht.trx_hash, 'escape')
    END
  ) _trx_id,
  (
    CASE
    WHEN ht.trx_in_block IS NULL THEN 4294967295
    ELSE ht.trx_in_block
    END
  ) _trx_in_block,
  T.op_pos::INT _op_in_trx,
  T.is_virtual _virtual_op,
  trim(both '"' from to_json(hb.created_at)::text) _timestamp,
  T.body _value,
  0 _operation_id
  FROM
  (
    SELECT
      ho.block_num, ho.trx_in_block, ho.op_pos, ho.body, ho.op_type_id, hot.is_virtual
      FROM hive_operations ho
      JOIN hive_account_operations hao ON ho.id = hao.operation_id
      JOIN hive_operation_types hot ON hot.id = ho.op_type_id
      WHERE ho.block_num = _BLOCK_NUM AND ( _OP_TYPE = 0 OR ( _OP_TYPE = 1 AND hot.is_virtual = FALSE ) OR ( _OP_TYPE = 2 AND hot.is_virtual = TRUE ) )
  ) T
  JOIN hive_blocks hb ON hb.num = T.block_num
  LEFT JOIN hive_transactions ht ON T.block_num = ht.block_num AND T.trx_in_block = ht.trx_in_block;

END
$function$
language plpgsql STABLE;

