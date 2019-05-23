#pragma once

namespace steem { namespace protocol {

enum curve_id
{
   quadratic,
   bounded_curation,
   linear,
   square_root,
   convergent_linear
};

} } // steem::utilities


FC_REFLECT_ENUM(
   steem::protocol::curve_id,
   (quadratic)
   (bounded_curation)
   (linear)
   (square_root)
   (convergent_linear)
)
