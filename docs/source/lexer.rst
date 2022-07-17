Using the lexer
===============

:func:`.parse_msd` is sufficient for most use cases.
However, **msdparser** exposes the underlying lexer, :func:`.lex_msd`, as a part of its public API for advanced use cases.

Some of those use cases might include...

* You want to edit simfiles while preserving whitespace & comments.
* You only need the metadata at the top of the file and want to stop at the first :code:`NOTES` key, without also reading the note data.
* You are streaming data from an untrusted source and want to avoid consuming unbounded input.
* Your application is user-facing and you want to pass control back to the main loop more consistently than :func:`.parse_msd`.

.. autoclass:: msdparser.lexer.lex_msd
    :noindex:

State diagram
-------------

.. image:: _static/lexer-diagram.png
  :width: 600
  :alt: Lexer state diagram

Inside of a parameter (between the :code:`#` and :code:`;`),
text, :code:`:` separators, :code:`\\` escapes, and :code:`//` comments are all valid.
Outside of a parameter, only text and comments are valid.
"Text" includes whitespace, such as line breaks, which will commonly be found between parameters.
