.. py:currentmodule:: bamboo_stash

Usage
=====

Basic Usage
-----------

.. code:: python
          
   from bamboo_stash import Stash
          
   stash = Stash()

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

If you want to control exactly where the cached data is stored, you can pass an
explicit directory name to :py:class:`Stash`:

.. code:: python

   from bamboo_stash import Stash

   stash = Stash("./stash/")

   @stash
   def my_function():
       ...
   
