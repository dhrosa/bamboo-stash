Welcome to bamboo-stash's documentation!
========================================

Overview
========

``bamboo-stash`` is a Python library for automatically caching function calls,
similar to :py:func:`functools.cache`. You can use it in a similar way:

.. grid:: 2

   .. grid-item-card:: Using ``functools.cache``

      .. code:: python

         from functools import cache

         @cache
         def my_function():
             ...

   .. grid-item-card:: Using ``bamboo-stash``

      .. code:: python

         from bamboo_stash import Stash

         stash = Stash()

         @stash
         def my_function():
             ...

The key difference is that ``bamboo-stash`` is primarily designed for iterating
on ``pandas``-based code in a Jupyter notebook. To support this, ``bamboo-stash`` has the following features:

- **Function calls are cached into files**. This means that function calls will still be cached even if the kernel is restarted

- **Cache lookup is based not only on the function arguments, but also on the
  function source code itself**. This means that if you modify the source code
  of a decorated function, subsequent calls will use a new cache that is
  separate from the old code's cache. This lets you continue to iterate on your
  code without accidentally using cached data from an older version of your
  code. This also means that if you then revert back to an older version of your
  code, it will automatically switch back to the previous cache it was using!

- **Supports Series and DataFrame arguments, in addition to any hashable
  argument**. ``pandas`` arguments are hashed using
  :py:func:`pandas.util.hash_pandas_object`. This has reasonable performance
  even for large inputs. From a casual benchmark, hashing a 1 million row
  dataframe with mixes of numeric and string columns takes about 0.5 seconds. If
  you're reaching for this library, 0.5 seconds is probably much faster than
  recomputing your function result.


.. toctree::
   :caption: Contents:

   installation
   usage
   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
