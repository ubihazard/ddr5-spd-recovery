DDR5 SPD Database
=================

The dumps are grouped by manufacturer and RAM kit.

Each kit folder follows the naming scheme:

  * Full name, as advertised on its packaging material.
      * Lower case letters with spaces replaced with `-`.
      * `oem`, if RAM doesn’t have a marketing title.
  * Speed in MHz: `6000`.
  * Primary timing values (CAS, tRCD, tRP, tRAS) separated by `-`: `38-38-38-78`.
  * Operating voltage of the primary XMP or EXPO profile, or the fastest supported JEDEC profile: `1.25`.
  * Module rank and memory banks configuration: `1x8`.
  * Module size times number of modules in a kit: `16x2`.
  * Part number in square brackets: `[ctced532g6000hc38adc01]`.
      * Do not confuse individual RAM module part number as recorded in its SPD and the part number of the whole RAM kit, – they are different things (see below).

(Fields are separated by `_`.)

Inside a kit folder there are SPD dump(s), each named according to its part number and serial number: `ud5-6000_0104eef6.spd`.
