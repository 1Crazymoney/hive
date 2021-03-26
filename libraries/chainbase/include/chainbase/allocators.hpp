#pragma once

#include <boost/interprocess/managed_mapped_file.hpp>
#include <boost/interprocess/containers/map.hpp>
#include <boost/interprocess/containers/flat_set.hpp>
#include <boost/interprocess/containers/flat_map.hpp>
#include <boost/interprocess/containers/deque.hpp>
#include <boost/interprocess/containers/string.hpp>
#include <boost/interprocess/containers/vector.hpp>
#include <boost/interprocess/allocators/allocator.hpp>
#include <boost/interprocess/sync/interprocess_sharable_mutex.hpp>
#include <boost/interprocess/sync/sharable_lock.hpp>
#include <boost/interprocess/sync/file_lock.hpp>

#include <boost/thread.hpp>
#include <boost/thread/locks.hpp>

#include <type_traits>

namespace chainbase {

  namespace bip = boost::interprocess;

  template< typename T >
  using allocator = bip::allocator<T, bip::managed_mapped_file::segment_manager>;

  typedef boost::interprocess::interprocess_sharable_mutex read_write_mutex;
  typedef boost::interprocess::sharable_lock< read_write_mutex > read_lock;

  typedef boost::unique_lock< read_write_mutex > write_lock;

  using shared_string = bip::basic_string< char, std::char_traits< char >, allocator< char > >;

  template<typename T>
  using t_vector = typename bip::vector<T, allocator<T> >;

  template< typename FIRST_TYPE, typename SECOND_TYPE >
  using t_pair = std::pair< FIRST_TYPE, SECOND_TYPE >;

  template< typename FIRST_TYPE, typename SECOND_TYPE >
  using t_allocator_pair = allocator< t_pair< const FIRST_TYPE, SECOND_TYPE > >;

  template< typename KEY_TYPE, typename LESS_FUNC = std::less<KEY_TYPE>>
  using t_flat_set = typename bip::flat_set< KEY_TYPE, LESS_FUNC, allocator< KEY_TYPE > >;

  template< typename KEY_TYPE, typename VALUE_TYPE, typename LESS_FUNC = std::less<KEY_TYPE>>
  using t_flat_map = typename bip::flat_map< KEY_TYPE, VALUE_TYPE, LESS_FUNC, allocator< t_pair< KEY_TYPE, VALUE_TYPE > > >;

  template< typename T >
  using t_deque = typename bip::deque< T, allocator< T > >;
}
