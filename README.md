# Pardef - A tool for generating flashable parameter Container

The basic idea is to develop a tool that is usable in embedded projects for
generation of parameters that are stored in flash memory independent from the
main application. The tool shall 

  * Read input from a schema validated XML file
  * Generate C-Source stubs for embedding into the application source core
  * Generate Intel Hex files for flashing with a programmer
  * Generate GNU linker include file for mapping the parameter to absolute addresses
  * Generate A2L fragements of accessing the parameters from AUTOSAR test environments
