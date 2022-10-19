# Description of conditions pygrambank commands check Grambank language coding sheets

There are two pygrambank commands that are run on language coding sheets upon submission to do a basic quality check: `sourcelookup` and `describe` (which calls `check`).

## describe
The coding sheet need to satisfy the following conditions:

* the filename is correct (valid coder abbreivation + underscore + valid glottocode .tsv)
* the coding sheet is separated by tabs (not commas)
* there are (at least) three columns named: Value, Comment and Source
* the values are valid (i.e. 1, 0, ?, 2, 3 depending on feature)
* if the column "Contributed_datapoint" is filled out, it contains valid coder abbreviations

## sourcelookup
Each coding sheet should have a column called "Source". The pygrambank sourcelookup command takes the content in this field (split by semi-colons if more than our source is listed) and attempts to match each source to a bibtex entry in either gb.bib or hh.bib (one of glottolog's bibliographies). The match is depedant on author name(s) and year. For the match to be succesful there needs to be a field in the bibtecx-entry called `lgcode` which contains a glottocode or ISO 639-3 code that matches to the glottocode in the filename of the coding sheet.

If there is more than one publication with the same author(s), year and lgcode we differentiate them by using a unique word from the title. This is done by author_UNIQUE WORD YEAR, for example: `Shaver_relaciones 1982`. 

If the source contains the string "p.c", it is ignored for further scrutiny. It is not matched to an entry in gb.bib or hh.bib.
