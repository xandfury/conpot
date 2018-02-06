=============
Databus
=============

Databus is one of the core feature of Conpot. It is responsible for carrying all the data around from various enabled protocols to hpfeeds or respective data volumes. Databus consists of key value pairs defined in the templates created or used.

The idea here is that when an attacker attacks Conpot, we can store both values and functions in the key value store functions could be used if a profile wants to simulate a sensor, or the function could interface with a real sensor

Snippet from default template:

For every key defined in the databus block, a corresponding value is given. These are used in by various running protocols.
The databus is managed by Conpots's SessionManager. For every instance, as soon as it starts, the get_sessionManager returns the instance of SessionManager and initialized with
