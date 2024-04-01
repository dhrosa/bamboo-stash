.. py:currentmodule:: bamboo_stash

Usage
=====

Basic Usage
-----------

.. code:: python

   from bamboo_stash import stash

   @stash
   def my_function():
       ...

The above code will automatically chose a standardized directory to store cached
data. For example on most Linux setups, the cached data will be stored in
:file:`~/.cache/bamboo-stash/`. To see where exactly the data is being stored,
`bamboo-stash` will show the directory it's using in its log output. You can
also print the value of :py:attr:`Stash.base_dir` in your code.


Advanced Usage
--------------

Choosing the cache directory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you want to control exactly where the cached data is stored, you can
explicitly instantiate a :py:class:`Stash` object and pass it a directory name:

.. code:: python

   from bamboo_stash import Stash

   stash = Stash("./stash/")

   @stash
   def my_function():
       ...

Locating and deleting cached files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Functions decorated with ``bamboo-stash`` become :py:class:`StashedFunction`
objects, which have extra attributes and methods for managing cached data.

If you want to manually locate where a specific function call's data is being
cached, you can use :py:meth:`StashedFunction.path_for`:

.. code:: python

   from bamboo_stash import stash

   @stash
   def my_function(x, y):
       ...

   z = f(1, 2)

   # This shows where the data for f(1, 2) is cached
   print(f.path_for(1, 2))


If you want to clear the cached data for a specific function call (e.g. to time
the original function), you can use :py:meth:`StashedFunction.clear_for`:

.. code:: python

   # Deletes cached data for f(1, 2).
   f.clear_for(1, 2)

You can also clear cached data for all calls to a specific function using
:py:meth:`StashedFunction.clear`:

.. code:: python

   f.clear()

And if you explicitly create a :py:class:`Stash` object, you can use
:py:meth:`Stash.clear` to delete cached data for all stashed functions.
