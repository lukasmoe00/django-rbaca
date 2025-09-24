FAQ
===

Q: How do I start the pipeline as a developer?
----------------------------------------------

A: If your commit message contains the flag "--mwps" at the end of the commit message, CI/CD will start a
pipeline on that commit automatically after pushing. You can also go into the merge request and press a button
to merge automatically when the pipeline succeeds.

Q: How do I build the documentation locally?
-----------------------------------

A: Install the requirements with poetry, move into the documentation folder and run

.. code-block:: bash

    make html
