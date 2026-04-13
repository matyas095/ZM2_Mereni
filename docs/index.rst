ZM2_Mereni — dokumentace
========================

Nástroj pro statistické zpracování fyzikálních laboratorních měření.

.. toctree::
   :maxdepth: 2
   :caption: Obsah:

   metody/index
   api/index
   shell_completion

Přehled
-------

Projekt je postaven na plugin architektuře v OOP. Každá metoda dědí z abstraktní třídy ``Method``. Data jsou zpracovávána prostřednictvím objektového modelu (``Measurement``, ``MeasurementSet``, ``InputParser``).

Balíky
------

* **Statistika** — výpočetní metody (průměr, chyba, propagace, konverze).
* **Grafy** — vizualizační metody (2D/3D grafy, histogramy, interval).

Indexy a tabulky
================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
