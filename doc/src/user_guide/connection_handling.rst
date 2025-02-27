.. _connhandling:

*****************************
Connecting to Oracle Database
*****************************

Connections between python-oracledb and Oracle Database are used for executing
:ref:`SQL <sqlexecution>` and :ref:`PL/SQL <plsqlexecution>`, for calling
:ref:`SODA <sodausermanual>` functions, for receiving database
:ref:`notifications <cqn>` and :ref:`messages <aqusermanual>`, and for
:ref:`starting and stopping <startup>` the database.

This chapter covers python-oracledb's synchronous programming model. For
discussion of asynchronous programming, see :ref:`asyncio`.

By default, python-oracledb runs in a 'Thin' mode which connects directly to
Oracle Database.  This mode does not need Oracle Client libraries.  However,
some :ref:`additional functionality <featuresummary>` is available when
python-oracledb uses them.  Python-oracledb is said to be in 'Thick' mode when
Oracle Client libraries are used.  See :ref:`enablingthick`.  Both modes have
comprehensive functionality supporting the Python Database API v2.0
Specification.

If you intend to use the Thick mode, then you *must* call
:func:`~oracledb.init_oracle_client()` in the application before any standalone
connection or pool is created.  The python-oracledb Thick mode loads Oracle
Client libraries which communicate over Oracle Net to an existing database.
The Oracle Client libraries need to be installed separately.  See
:ref:`installation`.  Oracle Net is not a separate product: it is how the
Oracle Client and Oracle Database communicate.

There are two ways to create a connection to Oracle Database using
python-oracledb:

*  **Standalone connections**: :ref:`Standalone connections <standaloneconnection>`
   are useful when the application needs a single connection to a database.
   Connections are created by calling :meth:`oracledb.connect()`.

*  **Pooled connections**: :ref:`Connection pooling <connpooling>` is important for
   performance when applications frequently connect and disconnect from the database.
   Pools support Oracle's :ref:`high availability <highavailability>` features and are
   recommended for applications that must be reliable.  Small pools can also be
   useful for applications that want a few connections available for infrequent
   use.  Pools are created with :meth:`oracledb.create_pool()` at application
   initialization time, and then :meth:`ConnectionPool.acquire()` can be called to
   obtain a connection from a pool.

Many connection behaviors can be controlled by python-oracledb connection
options.  Other settings can be configured in :ref:`optnetfiles` or in
:ref:`optclientfiles`.  These include limiting the amount of time that opening
a connection can take, or enabling :ref:`network encryption <netencrypt>`.

.. note::

       Creating a connection in python-oracledb Thin mode always requires a
       connection string, or the database host name and service name, to be
       specified.  The Thin mode cannot use "bequeath" connections and does not
       reference Oracle environment variables ``ORACLE_SID``, ``TWO_TASK``,
       or ``LOCAL``.

.. note::

       When using python-oracledb in Thin mode, the ``tnsnames.ora`` file will not
       be automatically located.  The file's directory must explicitly be passed
       to the application, see :ref:`optnetfiles`.

.. _standaloneconnection:

Standalone Connections
======================

Standalone connections are database connections that do not use a
python-oracledb connection pool.  They are useful for simple applications that
use a single connection to a database.  Simple connections are created by
calling :meth:`oracledb.connect()` and passing:

- A database username
- The database password for that user
- A 'data source name' connection string, see :ref:`connstr`

Python-oracledb also supports :ref:`external authentication <extauth>` so
passwords do not need to be in the application.

Creating a Standalone Connection
--------------------------------

Standalone connections are created by calling :meth:`oracledb.connect()`.

A simple standalone connection example:

.. code-block:: python

    import oracledb
    import getpass

    userpwd = getpass.getpass("Enter password: ")

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb")

You could alternatively read the password from an environment variable:

.. code-block:: python

    userpwd = os.environ.get("PYTHON_PASSWORD")

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="localhost/orclpdb")

The :meth:`oracledb.connect()` method allows the database host name and
database service name to be passed as separate parameters.  The database
listener port can also be passed:

.. code-block:: python

    import os

    userpwd = os.environ.get("PYTHON_PASSWORD")

    connection = oracledb.connect(user="hr", password=userpwd,
                                  host="localhost", port=1521, service_name="orclpdb")

If you like to encapsulate values, parameters can be passed using a
:ref:`ConnectParams Object <usingconnparams>`:

.. code-block:: python

    params = oracledb.ConnectParams(host="my_host", port=my_port, service_name="my_service_name")
    conn = oracledb.connect(user="my_user", password="my_password", params=params)

Some values such as the database host name can be specified as ``connect()``
parameters, as part of the connect string, and in the ``params`` object. If a
``dsn`` is passed, a connection string is internally constructed from the
individual parameters and ``params`` object values, with the individual
parameters having precedence. The precedence is that values in any ``dsn``
parameter override values passed as individual parameters, which themselves
override values set in the ``params`` object. Similar precedence rules also
apply to other values.

A single, combined connection string can be passed to ``connect()`` but this
may cause complications if the password contains "@" or "/" characters:

.. code-block:: python

    username="hr"
    userpwd = os.environ.get("PYTHON_PASSWORD")
    host = "localhost"
    port = 1521
    service_name = "orclpdb"

    dsn = f'{username}/{userpwd}@{host}:{port}/{service_name}'
    connection = oracledb.connect(dsn)

Closing Connections
+++++++++++++++++++

Connections should be released when they are no longer needed. You may prefer
to let connections be automatically cleaned up when references to them go out
of scope. This lets python-oracledb close dependent resources in the correct
order. For example, you can use a Python `context manager
<https://docs.python.org/3/library/stdtypes.html#context-manager-types>`__
``with`` block:

.. code-block:: python

    with oracledb.connect(user="hr", password=userpwd, dsn="myhostname/orclpdb") as connection:
        with connection.cursor() as cursor:
            cursor.execute("insert into SomeTable values (:1)", ("Some string"))
            connection.commit()

This code ensures that once the block is completed, the connection is closed
and resources have been reclaimed by the database. In addition, any attempt to
use the variable ``connection`` outside of the block will simply fail.

Alternatively, you can explicitly close a connection by calling.
:meth:`Connection.close()`:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd, dsn="localhost/orclpdb")

    # do something with the connection
    . . .

    # close the connection
    connection.close()

If you explicitly close connections you may also need to close other resources
first.

.. _connerrors:

Common Connection Errors
------------------------

Some of the common connection errors that you may encounter in the
python-oracledb's default Thin mode are detailed below.  Also see
:ref:`errorhandling`.

Use keyword parameters
++++++++++++++++++++++

If you use:

.. code-block:: python

    connection = oracledb.connect("hr", userpwd, "localhost/orclpdb")

then you will get the error::

    TypeError: connect() takes from 0 to 1 positional arguments but 3 were given

The :meth:`oracledb.connect()` method requires keyword parameters to be used

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd, dsn="localhost/orclpdb")

The exception passing a single argument containing the combined credential and
connection string.  This is supported:

.. code-block:: python

    connection = oracledb.connect("hr/userpwd@localhost/orclpdb")

Use the correct credentials
+++++++++++++++++++++++++++

If your username or password are not known by the database that you attempted
to connect to, then you will get the error::

    ORA-01017: invalid credential or not authorized; logon denied

Find the correct username and password and try reconnecting.

Use the correct connection string
+++++++++++++++++++++++++++++++++

If the hostname, port, or service name are incorrect, then the connection will fail
with the error::

    DPY-6001: cannot connect to database. Service "doesnotexist" is not
    registered with the listener at host "localhost" port 1521. (Similar to
    ORA-12514)

This error means that Python successfully reached a computer (in this case,
"localhost" using the default port 1521) that is running a database.  However,
the database service you wanted ("doesnotexist") does not exist there.

Technically, the error means the listener does not know about the service at the
moment.  So you might also get this error if the database is currently restarting.

This error is similar to the ``ORA-12514`` error that you may see when connecting
with python-oracledb in Thick mode, or with some other Oracle tools.

The solution is to use a valid service name in the connection string. You can:

- Check and fix any typos in the service name you used

- Check if the hostname and port are correct

- Ask your database administrator (DBA) for the correct values

- Wait a few moments and re-try in case the database is restarting

- Review the connection information in your cloud console or cloud wallet, if
  you are using a cloud database

- Run `lsnrctl status` on the database machine to find the known service names


.. _connstr:

Oracle Net Services Connection Strings
======================================

The data source name parameter ``dsn`` of :meth:`oracledb.connect()`,
:meth:`oracledb.create_pool()`, :meth:`oracledb.connect_async()`, and
:meth:`oracledb.create_pool_async()`, is the Oracle Database Oracle Net
Services Connection String (commonly abbreviated as "connection string") that
identifies which database service to connect to.  The ``dsn`` value can be one
of Oracle Database's naming methods:

* An Oracle :ref:`Easy Connect <easyconnect>` string
* A :ref:`Connect Descriptor <conndescriptor>`
* A :ref:`TNS Alias <netservice>` mapping to a Connect Descriptor in a
  :ref:`tnsnames.ora <optnetfiles>` file
* An :ref:`LDAP URL <ldapurl>`
* A :ref:`Configuration Provider URL <configproviderurl>`

Connection strings used for JDBC and Oracle SQL Developer need to be altered to
be usable as the ``dsn`` value, see :ref:`jdbcconnstring`.

For more information about naming methods, see the `Database Net Services
Administrator's Guide
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-E5358DEA-D619-4B7B-A799-3D2F802500F1>`__.

.. _easyconnect:

Easy Connect Syntax for Connection Strings
------------------------------------------

An `Easy Connect <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-59956F00-4996-4943-8D8B-9720DC67AD5D>`__ string is often the simplest
connection string to use in the data source name parameter ``dsn`` of
connection functions such as :meth:`oracledb.connect()` and
:meth:`oracledb.create_pool()`.  This method does not need configuration files
such as :ref:`tnsnames.ora <optnetfiles>`.

For example, to connect to the Oracle Database service ``orclpdb`` that is
running on the host ``dbhost.example.com`` with the default Oracle
Database port 1521, use:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb")

If the database is using a non-default port, it must be specified:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com:1984/orclpdb")

The Easy Connect syntax supports Oracle Database service names.  It cannot be
used with the older System Identifiers (SID).

The `Easy Connect <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-8C85D289-6AF3-41BC-848B-BF39D32648BA>`__ syntax allows the use of
multiple hosts or ports, along with optional entries for the wallet location,
the distinguished name of the database server, and allows some network
configuration options such as the connection timeout and keep-alive values to
be set::

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb?expire_time=2")

This means that a :ref:`sqlnet.ora <optnetfiles>` file is not needed for common
connection scenarios. See the technical brief `Oracle Database Easy Connect
Plus <https://download.oracle.com/ocomdocs/global/Oracle-Net-Easy
-Connect-Plus.pdf>`__ for additional information.

Python-oracledb specific settings can also be passed as Easy Connect arguments.
For example to set the statement cache size used by connections::

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb?pyo.stmtcachesize=50")

See :ref:`defineconnparams` and :ref:`definepoolparams` for the settings that
can be passed as arguments.

Any Easy Connect parameters that are unknown to python-oracledb are ignored and
not passed to the database.  See :ref:`Connection String Differences
<diffconnstr>` for more information.

.. _conndescriptor:

Connect Descriptors
-------------------

Connect Descriptors can be embedded directly in python-oracledb applications,
or referenced via a :ref:`TNS Alias <netservice>`.

An example of direct use is:

.. code-block:: python

    dsn = """(DESCRIPTION=
                 (FAILOVER=on)
                 (ADDRESS_LIST=
                   (ADDRESS=(PROTOCOL=tcp)(HOST=sales1-svr)(PORT=1521))
                   (ADDRESS=(PROTOCOL=tcp)(HOST=sales2-svr)(PORT=1521)))
                 (CONNECT_DATA=(SERVICE_NAME=sales.example.com)))"""

    connection = oracledb.connect(user="hr", password=userpwd, dsn=dsn)

The :meth:`oracledb.ConnectParams()` and
:meth:`ConnectParams.get_connect_string()` functions can be used to construct a
connect descriptor from the individual components, see :ref:`usingconnparams`.
For example:

.. code-block:: python

    cp = oracledb.ConnectParams(host="dbhost.example.com", port=1521, service_name="orclpdb")
    dsn = cp.get_connect_string()
    print(dsn)

This prints::

    (DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(HOST=dbhost.example.com)(PORT=1521)))(CONNECT_DATA=(SERVICE_NAME=orclpdb))(SECURITY=(SSL_SERVER_DN_MATCH=True)))

The ``CONNECT_DATA`` parameters of a full connect descriptor that are
unrecognized by python-oracledb are passed to the database unchanged.

.. _netservice:

TNS Aliases for Connection Strings
----------------------------------

:ref:`Connect Descriptors <conndescriptor>` are commonly stored in a
:ref:`tnsnames.ora <optnetfiles>` file and associated with a TNS Alias.  This
alias can be used directly for the data source name parameter ``dsn`` of
:meth:`oracledb.connect()` and :meth:`oracledb.create_pool()`.  For example,
given a file ``/opt/oracle/config/tnsnames.ora`` with the following contents::

    ORCLPDB =
      (DESCRIPTION =
        (ADDRESS = (PROTOCOL = TCP)(HOST = dbhost.example.com)(PORT = 1521))
        (CONNECT_DATA =
          (SERVER = DEDICATED)
          (SERVICE_NAME = orclpdb)
        )
      )

Then you could connect in python-oracledb Thin mode by passing the TNS Alias
"ORCLPDB" (case insensitive) as the ``dsn`` value:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd, dsn="orclpdb",
                                  config_dir="/opt/oracle/config")

More options for how python-oracledb locates ``tnsnames.ora`` files are
detailed in :ref:`optnetfiles`.  Note that in python-oracledb Thick mode, the
configuration directory must be set during initialization, not at connection
time.

TNS Aliases may also be resolved by :ref:`LDAP <ldapconnections>`.

For more information about Net Service Names, see `Database Net Services
Reference <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-
12C94B15-2CE1-4B98-9D0C-8226A9DDF4CB>`__.

.. _ldapurl:

LDAP URL Connection Strings
---------------------------

Oracle Client 23ai introduced support for LDAP URLs to be used as connection
strings. This syntax removes the need for external ``ldap.ora`` and
``sqlnet.ora`` files.  See the technical brief `Oracle Client 23ai LDAP URL
Syntax <https://www.oracle.com/a/otn/docs/database/oracle-net-23ai-ldap-url.
pdf>`__.  For example, python-oracledb Thick mode applications using Oracle
Client 23ai could connect using:

.. code-block:: python

    ldapurl = "ldaps://ldapserver.example.com/cn=orcl,cn=OracleContext,dc=example,dc=com"
    connection = oracledb.connect(user="scott", password=pw, dsn=ldapurl)

This syntax is also usable in python-oracledb Thin mode via a :ref:`connection
hook function <connectionhook>`, see :ref:`ldapconnections`.

.. _configproviderurl:

Centralized Configuration Provider URL Connection Strings
---------------------------------------------------------

A :ref:`Centralized Configuration Provider <configurationproviders>` URL
contains the details of where the configuration information is located. The
information that can be stored in configuration providers includes connect
descriptors, database credentials (user name and password), and python-oracledb
specific attributes. With this URL, python-oracledb can access the information
stored in the configuration providers listed below and connect to Oracle
Database:

- :ref:`Oracle Cloud Infrastructure (OCI) Object Storage configuration
  provider <ociobjstorage>`
- :ref:`Microsoft Azure App Configuration provider <azureappconfig>`
- :ref:`File Configuration Provider <fileconfigprovider>`

The configuration provider URL can be set in the ``dsn`` parameter of
connection functions :meth:`oracledb.connect()`,
:meth:`oracledb.create_pool()`, :meth:`oracledb.connect_async()`, and
:meth:`oracledb.create_pool_async()`. This URL must begin with
"config-<configuration-provider>" where the configuration-provider value can
be set to *ociobject*, *azure*, or *file*, depending on the location of your
configuration information. For example, to use connection configuration stored
in a local file ``/opt/oracle/my-config.json``, you need to specify the ``dsn``
parameter as shown:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                       dsn="config-file:///opt/oracle/my-config.json")

See the respective configuration provider sections for more details.

.. _jdbcconnstring:

JDBC and Oracle SQL Developer Connection Strings
------------------------------------------------

The python-oracledb connection string syntax is different from Java JDBC and the
common Oracle SQL Developer syntax.  If these JDBC connection strings reference
a service name like::

    jdbc:oracle:thin:@hostname:port/service_name

For example::

    jdbc:oracle:thin:@dbhost.example.com:1521/orclpdb

then use Oracle's Easy Connect syntax in python-oracledb:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com:1521/orclpdb")

You may need to remove JDBC-specific parameters from the connection string and
use python-oracledb alternatives.

If a JDBC connection string uses an old-style Oracle Database SID "system
identifier", and the database does not have a service name::

    jdbc:oracle:thin:@hostname:port:sid

For example::

    jdbc:oracle:thin:@dbhost.example.com:1521:orcl

then connect by using the ``sid`` parameter:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  host="dbhost.example.com", port=1521, sid="orcl")

Alternatively, create a ``tnsnames.ora`` entry (see :ref:`optnetfiles`), for
example::

    finance =
     (DESCRIPTION =
       (ADDRESS = (PROTOCOL = TCP)(HOST = dbhost.example.com)(PORT = 1521))
       (CONNECT_DATA =
         (SID = ORCL)
       )
     )

This can be referenced in python-oracledb:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd, dsn="finance")

.. _configurationproviders:

Centralized Configuration Providers
===================================

Centralized Configuration Providers allow the storage and management of
database connection credentials and application configuration information in a
central location. These providers allow you to separately store the
configuration information from the code of your application. The information
that can be stored in these providers includes connect descriptors, database
credentials such as user name and password, and python-oracledb specific
attributes.

You can access the information stored in configuration providers using both
python-oracledb Thin and Thick modes. With this information, python-oracledb
can connect to Oracle Database using :meth:`oracledb.connect()`,
:meth:`oracledb.create_pool()`, :meth:`oracledb.connect_async()`, or
:meth:`oracledb.create_pool_async()`.

The following configuration providers are supported by python-oracledb:

- :ref:`Oracle Cloud Infrastructure (OCI) Object Storage <ociobjstorage>`
- :ref:`Microsoft Azure App Configuration <azureappconfig>`
- :ref:`File Configuration Provider <fileconfigprovider>`

**Precedence of Attributes**

If you have defined the values of ``user`` and ``password`` in both the
application and the configuration provider, then the values defined in the
application will have the higher precedence. If the ``externalauth``
parameter is set to *True*, then the ``user`` and ``password`` values
specified in the configuration provider is ignored.

If you have defined the python-oracledb specific attributes in both the
application and in the configuration provider, then the values defined in the
configuration provider will have the higher precedence.

.. _ociobjstorage:

OCI Object Storage Configuration Provider
-----------------------------------------

The `Oracle Cloud Infrastructure (OCI) Object Storage <https://docs.oracle.com
/en-us/iaas/Content/Object/Concepts/objectstorageoverview.htm>`__ configuration
provider enables the storage and management of Oracle Database connection
information in a JSON file.

To use python-oracledb to access the configuration information from OCI Object
Storage, you must install the `OCI module <https://pypi.org/project/oci/>`__,
see :ref:`ocimodules`.

The JSON configuration file must contain the ``connect_descriptor`` property.
Optionally, you can specify the database user name, password, and
python-oracledb specific properties in the file. The database password can also
be stored securely as a secret using `OCI Vault <https://docs.oracle.com/en-us/
iaas/Content/KeyManagement/Tasks/managingsecrets.htm>`__. The properties that
can be added in the JSON file are listed below:

.. list-table-with-summary:: JSON Properties for OCI Object Storage Configuration Provider
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 15 25 15
    :name: _oci_object_storage_sub-objects
    :summary: The first column displays the name of the property. The second column displays the description of the property. The third column displays whether the property is required or optional.

    * - Property
      - Description
      - Required or Optional
    * - ``user``
      - The database user name.
      - Optional
    * - ``password``
      - The password of the database user, or a dictionary containing the key "type" and password-type specific properties.
      - Optional
    * - ``connect_descriptor``
      - The database :ref:`connection string <connstr>`.
      - Required
    * - ``pyo``
      - Python-oracledb specific properties.
      - Optional

The following sample is an example of OCI Object Storage configuration
provider syntax::

    {
        "user": "scott",
        "password": {
            "type": "oci-vault",
            "value": "oci.vaultsecret.my-secret-id"
            "authentication": "OCI_INSTANCE_PRINCIPAL"
        },
        "connect_descriptor": "dbhost.example.com:1522/orclpdb",
        "pyo": {
            "stmtcachesize": 30,
            "min": 2,
            "max": 10
        }
    }

If the password key has a reference to Azure Key Vault, then you must define
the Azure Key Vault credentials in the ``password`` property. The
``azure_client_id`` and ``azure_tenant_id`` must be specified in the password
property. Also, either the ``azure_client_secret`` or
``azure_client_certificate_path`` should be specified. The password format
should be::

    "password": {
            "type": "azure-vault",
            "value": "<Azure Key Vault URI>",
            "azure_tenant_id":"<tenant_id>",
            "azure_client_id":"<client_id>",
            "azure_client_secret": "<secret value>", or "azure_client_certificate_path" : "<azure_client_certificate_path>"
        }

.. _useociconfigprovider:

Using python-oracledb with OCI Object Storage Configuration Provider
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

To use python-oracledb with an OCI Object Storage configuration provider, you
must:

1. :ref:`Import the oracledb.plugins.oci_config_provider plugin
   <importconfigociplugin>` in your code.

2. :ref:`Use an OCI Object Storage connection string URL <connstringoci>`
   in the ``dsn`` parameter of connection and pool creation methods.

An example using a :ref:`standalone connection <standaloneconnection>` is
shown below:

.. code-block:: python

    import oracledb.plugins.oci_config_provider

    configociurl = "config-ociobject://abc.oraclecloud.com/n/abcnamespace/b/abcbucket/o/abcobject?oci_tenancy=abc123&oci_user=ociuser1&oci_fingerprint=ab:14:ba:13&oci_key_file=ociabc/ocikeyabc.pem"

    oracledb.connect(dsn=configociurl)

An example using a :ref:`connection pool <connpooling>` is shown below:

.. code-block:: python

    import oracledb.plugins.oci_config_provider

    configociurl = "config-ociobject://abc.oraclecloud.com/n/abcnamespace/b/abcbucket/o/abcobject?oci_tenancy=abc123&oci_user=ociuser1&oci_fingerprint=ab:14:ba:13&oci_key_file=ociabc/ocikeyabc.pem"

    oracledb.create_pool(dsn=configociurl)

.. _importconfigociplugin:

Importing ``oracledb.plugins.oci_config_provider``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You must import a :ref:`oracledb.plugins.oci_config_provider <configociplugin>`
plugin provided by python-oracledb to access the configuration information
stored in :ref:`OCI Object Storage <ociobjstorage>` such as database connect
descriptor, user name, password, and python-oracledb specific attributes.

Importing this plugin defines and
:meth:`registers <oracledb.register_protocol()>` a built-in
:ref:`connection hook function <connectionhook>` that handles :ref:`connection
strings prefixed with config-ociobject <connstringoci>`. This function is
internally invoked when the ``dsn`` parameter is prefixed with
``config-ociobject`` in calls to :meth:`oracledb.connect()`,
:meth:`oracledb.create_pool()`, :meth:`oracledb.connect_async()`, or
:meth:`oracledb.create_pool_async()`. This hook function parses the connection
string, and extracts the following details:

- URL of the OCI Object Storage endpoint
- OCI Object Storage namespace where the JSON file is stored
- OCI Object Storage bucket name where the JSON file is stored
- JSON file name
- Network service name or alias if the JSON file contains one or more aliases
- OCI Object Storage authentication details

Using the above details, the hook function accesses the configuration
information stored in OCI Object Storage.  The hook function sets the
connection information from OCI Object Storage in its ``connect_params``
parameter which is a :ref:`ConnectParams <connparam>` object. This object is
used by python-oracledb to establish a connection to Oracle Database.

.. _connstringoci:

Defining a Connection String URL for OCI Object Storage
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You must define a connection string URL in a specific format in the ``dsn``
property of :meth:`oracledb.connect()`, :meth:`oracledb.create_pool()`,
:meth:`oracledb.connect_async()`, or :meth:`oracledb.create_pool_async()` to
access the information stored in OCI Object Storage. The syntax of the OCI
Object Storage connection string URL is::

    config-ociobject:<objectstorage-name>/n/{namespaceName}/b/{bucketName}/o/
    <objectName>[/c/<networkServiceName>][?<option1>=<value1>&<option2>=<value2>...]

The parameters of the connection string are detailed in the table below.

.. list-table-with-summary:: Connection String Parameters for OCI Object Storage
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 15 25 15
    :name: _connection_string_for_oci_object_storage
    :summary: The first row displays the name of the connection string parameter. The second row displays whether the connection string parameter is required or optional. The third row displays the description of the connection string parameter.

    * - Parameter
      - Description
      - Required or Optional
    * - ``config-ociobject``
      - Indicates that the configuration provider is OCI Object Storage.
      - Required
    * - <objectstorage-name>
      - The URL of OCI Object Storage endpoint.
      - Required
    * - <namespaceName>
      - The OCI Object Storage namespace where the JSON file is stored.
      - Required
    * - <bucketName>
      - The OCI Object Storage bucket name where the JSON file is stored.
      - Required
    * - <objectName>
      - The JSON file name.
      - Required
    * - <networkServiceName>
      - The network service name or alias if the JSON file contains one or more network service names.
      - Optional
    * - <options> and <values>
      - The authentication method and corresponding authentication parameters to access the OCI Object Storage configuration provider. Depending on the specified authentication method, you must also set the corresponding authentication parameters in the ``option=value`` syntax of the connection string. You can specify one of the following authentication methods:

        - **API Key-based Authentication**: The authentication to OCI is done using API key-related values. This is the default authentication method. To use this method, you must set the option value to OCI_DEFAULT. Note that this value is also used when no authentication value is set.

         You can set optional authentication parameters for this method such as OCI_PROFILE, OCI_TENANCY, OCI_USER, OCI_FINGERPRINT, OCI_KEY_FILE, and OCI_PASS_PHRASE. See `Authentication Parameters for Oracle Cloud Infrastructure (OCI) Object Storage <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-EB94F084-0F3F-47B5-AD77-D111070F7E8D>`__. These authentication parameters can also be set in an OCI Authentication Configuration file which can be stored in a default location ~/.oci/config, or in location ~/.oraclebmc/config, or in the location specified by the OCI_CONFIG_FILE environment variable.

        - **Instance Principal Authentication**: The authentication to OCI is done using VM instance credentials running on OCI. To use this method, you must set the option value to OCI_INSTANCE_PRINCIPAL. There are no optional authentication parameters for this method.

        - **Resource Principal Authentication**: The authentication to OCI is done using OCI resource principals. To use this method, you must set the option value to OCI_RESOURCE_PRINCIPAL. There are no optional authentication parameters for this method.

        See `OCI Authentication Methods <https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_authentication_methods.htm>`__ for more information.
      - Optional

You can store the authentication details in an OCI Authentication Configuration
file which can be stored in a default location (~/.oci/config). The
``oci_from_file()`` method will check this location for the configuration file.
The OCI Object Storage configuration provider uses this method when the
default authentication method is specified or when the authentication details
are not provided in the connection string.

An example of a connection string for OCI Object Storage configuration provider
is shown below:

.. code-block:: python

    configociurl = "config-ociobject://abc.oraclecloud.com/n/abcnamespace/b/abcbucket/o/abcobject?oci_tenancy=abc123&oci_user=ociuser1&oci_fingerprint=ab:14:ba:13&oci_key_file=ociabc/ocikeyabc.pem"

.. _azureappconfig:

Azure App Configuration Provider
--------------------------------

`Azure App Configuration <https://learn.microsoft.com/en-us/azure/azure-app-
configuration/overview>`__ is a cloud-based service provided by Microsoft
Azure that enables the storage and management of Oracle Database connection
information. Your application must be registered with `Microsoft Entra ID
<https://www.microsoft.com/en-in/security/business/identity-access/microsoft
-entra-id>`__ (formerly Microsoft Azure Active Directory) and must have the
required authorization permissions to access the Azure App Configuration
provider.

To use python-oracledb to access the configuration information from Azure App
Configuration, you must install certain Microsoft Azure modules, see
:ref:`azuremodules`.

Configuration information is stored as key-value pairs in Azure App
Configuration. You must add the connect descriptor as a key under a prefix
based on the requirements of your application. Optionally, you can add the
database user name, password, and python-oracledb specific properties as keys.
The database password can be stored securely as a secret using `Azure Key Vault
<https://learn.microsoft.com/en-us/azure/key-vault/general/overview>`__. In
Azure App Configuration, you can add the following keys under a prefix:

- <prefix>connect_descriptor (required)
- <prefix>user (optional)
- <prefix>password (optional)
- <prefix>pyo(optional)

The key ending with:

- ``connect_descriptor`` stores the :ref:`connect descriptor <conndescriptor>`
  as the value.
- ``user`` stores the database user name as the value.
- ``password`` stores the reference to the Azure Key Vault and Secret as
  the value.
- ``pyo`` stores the values of the python-oracledb specific properties.

See `Oracle Net Service Administrator’s Guide <https://www.oracle.com/pls/
topic/lookup?ctx=dblatest&id=GUID-DBCA9021-F3E1-4B30-8F17-A98900299D73>`__ for
more information.

.. _azureappconfigexample:

The following table lists the sample configuration information defined in Azure
App Configuration as key-value pairs. Note that the key-value pairs are defined
under the same prefix ``test/`` as an example.

.. list-table-with-summary::
    :header-rows: 1
    :class: wy-table-responsive
    :align: center
    :widths: 30 70
    :name: _azure_app_configuration_keys_and_values
    :summary: The first row displays the name of the key defined in Azure App Configuration. The second row displays the value of the key defined in Azure App Configuration.

    * - Azure App Configuration Key
      - Value
    * - test/connect_descriptor
      - (description=(retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1521)(host=adb.region.oraclecloud.com))(connect_data=(service_name=cdb1_pdb1)))
    * - test/user
      - scott
    * - test/password
      - {"uri":"https://mykeyvault.vault.azure.net/secrets/passwordsalescrm"}
    * - test/pyo
      - {"stmtcachesize":30, "min":2, "max":10}

.. _useazureconfigprovider:

Using python-oracledb with Azure App Configuration Provider
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

To use python-oracledb with an Azure App Configuration provider, you must:

1. :ref:`Import the
   oracledb.plugins.azure_config_provider <importconfigazureplugin>` plugin in
   your code.

2. :ref:`Use an Azure App Configuration connection string URL
   <connstringazure>` in the ``dsn`` parameter of connection and pool creation
   methods.

An example using a :ref:`standalone connection <standaloneconnection>` is
shown below.

.. code-block:: python

    import oracledb.plugins.azure_config_provider

    configazureurl = "config-azure://aznetnamingappconfig.azconfig.io/?key=test/&azure_client_id=123-456&azure_client_secret=MYSECRET&azure_tenant_id=789-123"

    oracledb.connect(dsn=configazureurl)

An example using a :ref:`connection pool <connpooling>` is shown below.

.. code-block:: python

    import oracledb.plugins.azure_config_provider

    configazureurl = "config-azure://aznetnamingappconfig.azconfig.io/?key=test/&azure_client_id=123-456&azure_client_secret=MYSECRET&azure_tenant_id=789-123"

    oracledb.create_pool(dsn=configazureurl)

.. _importconfigazureplugin:

Importing ``oracledb.plugins.azure_config_provider``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You must import a :ref:`oracledb.plugins.azure_config_provider
<configazureplugin>` plugin provided by python-oracledb to access the
configuration information stored in Azure App Configuration such as database
connect descriptor, user name, password, and python-oracledb specific
attributes.

Importing this plugin defines and
:meth:`registers <oracledb.register_protocol()>` a built-in :ref:`connection
hook function <connectionhook>` that handles :ref:`connection strings prefixed
with config-azure <connstringazure>`. This function is internally invoked when
the ``dsn`` parameter is prefixed with ``config-azure`` in calls to
:meth:`oracledb.connect()`, :meth:`oracledb.create_pool()`,
:meth:`oracledb.connect_async()`, or :meth:`oracledb.create_pool_async()`. This
hook function parses the connection string, and extracts the following details:

- The URL of the Azure App Configuration endpoint
- The key prefix to identify the connection
- The Azure App Configuration label name
- Azure App Configuration authentication details

Using the above details, the hook function accesses the configuration
information stored in Azure App Configuration. The hook function sets the
connection information from Azure App Configuration in its ``connect_params``
parameter which is a :ref:`ConnectParams <connparam>` object. This object is
used by python-oracledb to establish a connection to Oracle Database.

.. _connstringazure:

Defining a Connection String URL for Azure App Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You must define a connection string URL in a specific format in the ``dsn``
property of :meth:`oracledb.connect()`, :meth:`oracledb.create_pool()`,
:meth:`oracledb.connect_async()`, or :meth:`oracledb.create_pool_async()` to
access the information stored in Azure App Configuration. The syntax of the
Azure App Configuration connection string URL is::

    config-azure://<appconfigname>[?key=<prefix>&label=<value>&<option1>=<value1>&<option2>=<value2>…]

The parameters of the connection string are detailed in the table below.

.. list-table-with-summary:: Connection String Parameters for Azure App Configuration
    :header-rows: 1
    :class: wy-table-responsive
    :align: center
    :widths: 15 25 15
    :name: _connection_string_for_azure_app
    :summary: The first row displays the name of the connection string parameter. The second row displays whether the connection string parameter is required or optional. The third row displays the description of the connection string parameter.

    * - Parameter
      - Description
      - Required or Optional
    * - config-azure
      - Indicates that the configuration provider is Azure App Configuration.
      - Required
    * - <appconfigname>
      - The URL of the Azure App configuration endpoint.
      - Required
    * - key=<prefix>
      - A key prefix to identify the connection. You can organize configuration information under a prefix as per application requirements.
      - Required
    * - label=<value>
      - The Azure App Configuration label name.
      - Optional
    * - <options>=<values>
      - The authentication method and corresponding authentication parameters to access the Azure App Configuration provider. Depending on the specified authentication method, you must also set the corresponding authentication parameters in the ``option=value`` syntax of the connection string. You can specify one of the following authentication methods:

        - **Default Azure Credential**: The authentication to Azure App Configuration is done as a service principal (using either a client secret or client certificate) or as a managed identity depending on which parameters are set. This authentication method also supports reading the parameters as environment variables. This is the default authentication method. To use this authentication method, you must set the option value to AZURE_DEFAULT. Note that this value is also used when no authentication value is set.

         There are no required parameters for this option value. The optional parameters include AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_CLIENT_CERTIFICATE_PATH, AZURE_TENANT_ID, and AZURE_MANAGED_IDENTITY_CLIENT_ID.

        - **Service Principal with Client Secret**: The authentication to Azure App Configuration is done using the client secret. To use this method, you must set the option value to AZURE_SERVICE_PRINCIPAL.

         The required parameters for this option include AZURE_SERVICE_PRINCIPAL, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, and AZURE_TENANT_ID. There are no optional parameters for this option value.

        - **Service Principal with Client Certificate**: The authentication to Azure App Configuration is done using the client certificate. To use this method, you must set the option value to AZURE_SERVICE_PRINCIPAL.

         The required parameters for this option are AZURE_SERVICE_PRINCIPAL, AZURE_CLIENT_ID, AZURE_CLIENT_CERTIFICATE_PATH, and AZURE_TENANT_ID. There are no optional parameters for this option value.

        - **Managed Identity**: The authentication to Azure App Configuration is done using managed identity or managed user identity credentials. To use this method, you must set the option value to AZURE_MANAGED_IDENTITY.

         If you want to use a user-assigned managed identity for authentication, then you must specify the required parameter AZURE_MANAGED_IDENTITY_CLIENT_ID. There are no optional parameters for this option value.

      - Optional

Note that the Azure service principal with client certificate overrides Azure
service principal with client secret. See `Authentication Parameters for Azure
App Configuration Store <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-1EECAD82-6CE5-4F4F-A844-C75C7AA1F907>`__ for more information.

An example of a connection string for Azure App Configuration provider is shown
below:

.. code-block:: python

    configazureurl = "config-azure://aznetnamingappconfig.azconfig.io/?key=test/&azure_client_id=123-456&azure_client_secret=MYSECRET&azure_tenant_id=789-123"

.. _fileconfigprovider:

Connecting Using the File Configuration Provider
------------------------------------------------

The file configuration provider enables the storage and management of Oracle
Database connection information as JSON in a file on your local file system.

When a connection or pool creation method is called with the prefix
``config-file://`` for its ``dsn`` parameter, a built-in :ref:`connection hook
function <connectionhook>` is internally invoked. This function parses the DSN
and loads the configuration information which is stored in the specified file
as JSON.  The hook function sets the connection information in its
``connect_params`` parameter. This :ref:`ConnectParams <connparam>` object is
used by python-oracledb to establish a connection to Oracle Database.

The configuration file must contain at least the database connection
string. Optionally, you can add the database user name, password, and
python-oracledb specific properties. The JSON properties that can be added to
the file are listed in the table below.

.. list-table-with-summary:: JSON properties for the File Configuration Provider
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 15 25 15
    :name: _file_configuration_provider
    :summary: The first column displays the name of the property. The second column displays its description. The third column displays whether the sub-object is required or optional.

    * - Property
      - Description
      - Required or Optional
    * - ``user``
      - The database user name.
      - Optional
    * - ``password``
      - The password of the database user, or a dictionary containing the key "type" and password type-specific properties.
      - Optional
    * - ``connect_descriptor``
      - The database :ref:`connection string <connstr>`.
      - Required
    * - ``pyo``
      - Python-oracledb specific properties.
      - Optional

See the `Oracle Net Service Administrator’s Guide <https://www.oracle.com/pls/
topic/lookup?ctx=dblatest&id=GUID-B43EA22D-5593-40B3-87FC-C70D6DAF780E>`__ for
more information on these sub-objects.

.. warning::

    Storing passwords in the configuration file should only ever be used in
    development or test environments.

    When using the password type handler for "base64", a warning message will
    be generated: "base64 encoded passwords are insecure".

**Sample File Configuration Provider syntax**

.. _singlefileconfiguration:

The following sample is an example of the File Configuration Provider syntax::

    {
        "user": "scott",
        "password": {
            "type": "base64",
            "value": "dGlnZXI="
        },
        "connect_descriptor": "dbhost.example.com:1522/orclpdb",
        "pyo": {
            "stmtcachesize": 30,
            "min": 2,
            "max": 10
        }
    }

.. _multiplefileconfigurations:

Multiple configurations can be defined by using keys as shown in the example
below. The key values are user-chosen::

    {
        "production": {
            "connect_descriptor": "localhost/orclpdb"
        },
        "testing": {
            "connect_descriptor": "localhost/orclpdb",
            "user": "scott",
            "password": {
                "type": "base64",
                "value": "dGlnZXI="
            }
        }
    }

Using python-oracledb with a File Configuration Provider
++++++++++++++++++++++++++++++++++++++++++++++++++++++++

To use a provider file, specify the ``dsn`` parameter of
:meth:`oracledb.connect()`, :meth:`oracledb.create_pool()`,
:meth:`oracledb.connect_async()`, or :meth:`oracledb.create_pool_async()` using
the following format::

    config-file://<file-path-and-name>[?key=<key>]

The parameters of the ``dsn`` parameter are detailed in the table below.

.. list-table-with-summary:: Connection String Parameters for File Configuration Provider
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 20 60
    :name: _connection_string_for_file_configuration_provider
    :summary: The first column displays the name of the connection string parameter. The second column displays the description of the connection string parameter.

    * - Parameter
      - Description
    * - ``config-file``
      - Indicates that the centralized configuration provider is a file in your local system.
    * - <file-name>
      - The file path (absolute or relative path) and name of the JSON file that contains the configuration information. For relative paths, python-oracledb will use the ``config_dir`` value to create an absolute path.
    * - ``key``
      - The connection key name used to identify a specific configuration. If this parameter is specified, the file is assumed to contain multiple configurations that are indexed by the key. If not specified, the file is assumed to contain a single configuration.

For example, if you have a configuration file in
``/opt/oracle/my-config1.json`` with a :ref:`single configuration
<singlefileconfiguration>` you could use it like:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                       dsn="config-file:///opt/oracle/my-config1.json")

If you have a configuration file in ``/opt/oracle/my-config2.json`` with
:ref:`multiple configurations <multiplefileconfigurations>` you could use it like:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                 dsn="config-file:///opt/oracle/my-config2.json?key=production")


.. _usingconnparams:

Using the ConnectParams Builder Class
======================================

The :ref:`ConnectParams class <connparam>` allows you to define connection
parameters in a single place.  The :func:`oracledb.ConnectParams()` function
returns a ``ConnectParams`` object.  The object can be passed to
:func:`oracledb.connect()`. For example:

.. code-block:: python

    cp = oracledb.ConnectParams(user="hr", password=userpwd,
                                host="dbhost", port=1521, service_name="orclpdb")
    connection = oracledb.connect(params=cp)

The use of the ConnectParams class is optional because you can pass the same
parameters directly to :func:`~oracledb.connect()`.  For example, the code above
is equivalent to:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  host="dbhost", port=1521, service_name="orclpdb")


If you want to keep credentials separate, you can use ConnectParams just to
encapsulate connection string components:

.. code-block:: python

    cp = oracledb.ConnectParams(host="dbhost", port=1521, service_name="orclpdb")
    connection = oracledb.connect(user="hr", password=userpwd, params=cp)

You can use :meth:`ConnectParams.get_connect_string()` to get a connection
string from a ConnectParams object:

.. code-block:: python

    cp = oracledb.ConnectParams(host="dbhost", port="my_port", service_name="my_service_name")
    dsn = cp.get_connect_string()
    connection = oracledb.connect(user="hr", password=userpwd, dsn=dsn)

To parse a connection string and store components as attributes:

.. code-block:: python

    cp = oracledb.ConnectParams()
    cp.parse_connect_string("host.example.com:1522/orclpdb")

Most parameter values of :func:`oracledb.ConnectParams()` are gettable as
attributes. For example, to get the stored host name:

.. code-block:: python

    print(cp.host)

Attributes such as the password are not gettable.

You can set individual default attributes using :meth:`ConnectParams.set()`:

.. code-block:: python

    cp = oracledb.ConnectParams(host="localhost", port=1521, service_name="orclpdb")

    # set a new port
    cp.set(port=1522)

    # change both the port and service name
    cp.set(port=1523, service_name="orclpdb")

Note :meth:`ConnectParams.set()` has no effect after
:meth:`ConnectParams.parse_connect_string()` has been called.

Some values such as the database host name can be specified as
:func:`oracledb.connect()`, parameters, as part of the connect string, and in
the ``params`` object.  If a ``dsn`` is passed, a connection string is
internally constructed from the individual parameters and ``params`` object
values, with the individual parameters having precedence. The precedence is
that values in any ``dsn`` parameter override values passed as individual
parameters, which themselves override values set in the ``params`` object.
Similar precedence rules also apply to other values.

The :meth:`ConnectParams.parse_dsn_with_credentials()` can be used to extract
the username, password and connection string from a DSN:

.. code-block:: python

    cp = oracledb.ConnectParams()
    (un,pw,cs) = cp.parse_dsn_with_credentials("scott/tiger@localhost/orclpdb")

Empty values are returned as ``None``.

The :meth:`ConnectParams.get_network_service_names()` can be used to get a
list of the network service names that are defined in the
:ref:`tnsnames.ora <optnetfiles>` file. The directory that contains the
tnsnames.ora file can be specified in the :attr:`~ConnectParams.config_dir`
attribute.

.. code-block:: python

    cp = oracledb.ConnectParams(host="my_host", port=my_port, dsn="orclpdb",
                                config_dir="/opt/oracle/config")
    cp.get_network_service_names()

If the :meth:`ConnectParams.get_network_service_names()` method is called but
a tnsnames.ora file does not exist, then an error such as the following is
returned::

    DPY-4026: file tnsnames.ora not found in /opt/oracle/config

If :attr:`~ConnectParams.config_dir` is not specified, then the following
error is returned::

    DPY-4027: no configuration directory specified

When creating a standalone connection or connection pool the equivalent
internal extraction is done automatically when a value is passed to the ``dsn``
parameter of :meth:`oracledb.connect()` or :meth:`oracledb.create_pool()` but
no value is passed to the ``user`` password.

.. _defineconnparams:

Defining ConnectParams Parameters in a Connection String
--------------------------------------------------------

You can specify certain common parameters of the :ref:`ConnectParams object
<connparam>` directly in an :ref:`Easy Connect string <easyconnect>`. This can
be done by using the question mark symbol (?) to indicate the start of the
parameter-value pairs and the ampersand symbol (&) to delimit each
parameter-value pair. For example:

.. code-block:: python

    cp = oracledb.ConnectParams()
    cp.parse_connect_string("host.example.com:1522/orclpdb?transport_connect_timeout=15&retry_count=5&retry_delay=5")

The common ConnectParams parameters that can be set in a connection string are
listed in the table below:

.. list-table-with-summary:: Common ConnectParams Parameters
    :header-rows: 1
    :class: wy-table-responsive
    :align: center
    :widths: 10 10 10
    :name: _common_parameters
    :summary: The first column displays the name of the connect string parameter name. The second column displays the Python parameter name. The third column displays the type of the parameter.

    * - Connect String Parameter Name
      - Python Parameter Name
      - Type
    * - EXPIRE_TIME
      - :attr:`~ConnectParams.expire_time`
      - integer
    * - HTTPS_PROXY
      - :attr:`~ConnectParams.https_proxy`
      - string
    * - HTTPS_PROXY_PORT
      - :attr:`~ConnectParams.https_proxy_port`
      - integer
    * - POOL_BOUNDARY
      - :attr:`~ConnectParams.pool_boundary`
      - string
    * - POOL_CONNECTION_CLASS
      - :attr:`~ConnectParams.cclass`
      - string
    * - POOL_PURITY
      - :attr:`~ConnectParams.purity`
      - oracledb.Purity
    * - RETRY_COUNT
      - :attr:`~ConnectParams.retry_count`
      - integer
    * - RETRY_DELAY
      - :attr:`~ConnectParams.retry_delay`
      - integer
    * - SDU
      - :attr:`~ConnectParams.sdu`
      - integer
    * - SSL_SERVER_DN_MATCH
      - :attr:`~ConnectParams.ssl_server_dn_match`
      - boolean
    * - SSL_SERVER_CERT_DN
      - :attr:`~ConnectParams.ssl_server_cert_dn`
      - string
    * - TRANSPORT_CONNECT_TIMEOUT
      - :attr:`~ConnectParams.tcp_connect_timeout`
      - integer
    * - WALLET_LOCATION
      - :attr:`~ConnectParams.wallet_location`
      - string

Also, you can specify additional parameters of the :ref:`ConnectParams object
<connparam>` directly in an :ref:`Easy Connect string <easyconnect>`. This can
be done by using the question mark symbol (?) to indicate the start of the
parameter-value pairs and the ampersand symbol (&) to delimit each
parameter-value pair. Addiitionally, you must define each parameter name with
the prefix "pyo.". For example:

.. code-block:: python

    cp = oracledb.ConnectParams()
    cp.parse_connect_string("host.example.com:1522/orclpdb?pyo.stmtcachesize=30&pyo.mode=SYSDBA")

Note that these parameters can only be added in Easy Connect strings and not
in :ref:`Connect Descriptors <conndescriptor>`.

The ConnectParams parameters that can be set in a connection string with the
prefix "pyo."" are listed in the table below:

.. list-table-with-summary:: Additional ConnectParams Parameters
    :header-rows: 1
    :class: wy-table-responsive
    :align: center
    :widths: 10 10 10
    :name: _additional_connectparams_parameters
    :summary: The first column displays the name of the connect string parameter name. The second column displays the Python parameter name. The third column displays the type of the parameter.

    * - Connect String Parameter Name
      - Python Parameter Name
      - Type
    * - PYO.CCLASS
      - :attr:`ConnectParams.cclass`
      - string
    * - PYO.CONNECTION_ID_PREFIX
      - :attr:`ConnectParams.connection_id_prefix`
      - string
    * - PYO.DISABLE_OOB
      - :attr:`ConnectParams.disable_oob`
      - boolean
    * - PYO.DRIVER_NAME
      - :attr:`~ConnectParams.driver_name`
      - string
    * - PYO.EDITION
      - :attr:`~ConnectParams.edition`
      - string
    * - PYO.EVENTS
      - :attr:`~ConnectParams.events`
      - boolean
    * - PYO.EXPIRE_TIME
      - :attr:`~ConnectParams.expire_time`
      - integer
    * - PYO.EXTERNALAUTH
      - :attr:`~ConnectParams.externalauth`
      - boolean
    * - PYO.HTTPS_PROXY
      - :attr:`~ConnectParams.https_proxy`
      - string
    * - PYO.HTTPS_PROXY_PORT
      - :attr:`~ConnectParams.https_proxy_port`
      - integer
    * - PYO.MACHINE
      - :attr:`~ConnectParams.machine`
      - string
    * - PYO.MODE
      - :attr:`~ConnectParams.mode`
      - oracledb.AuthMode
    * - PYO.OSUSER
      - :attr:`~ConnectParams.osuser`
      - string
    * - PYO.POOL_BOUNDARY
      - :attr:`~ConnectParams.pool_boundary`
      - string
    * - PYO.PROGRAM
      - :attr:`~ConnectParams.program`
      - string
    * - PYO.PURITY
      - :attr:`~ConnectParams.purity`
      - oracledb.Purity
    * - PYO.RETRY_COUNT
      - :attr:`~ConnectParams.retry_count`
      - integer
    * - PYO.RETRY_DELAY
      - :attr:`~ConnectParams.retry_delay`
      - integer
    * - PYO.SDU
      - :attr:`~ConnectParams.sdu`
      - integer
    * - PYO.SSL_SERVER_CERT_DN
      - :attr:`~ConnectParams.ssl_server_cert_dn`
      - string
    * - PYO.SSL_SERVER_DN_MATCH
      - :attr:`~ConnectParams.ssl_server_dn_match`
      - boolean
    * - PYO.STMTCACHESIZE
      - :attr:`~ConnectParams.stmtcachesize`
      - integer
    * - PYO.TCP_CONNECT_TIMEOUT
      - :attr:`~ConnectParams.tcp_connect_timeout`
      - integer
    * - PYO.TERMINAL
      - :attr:`~ConnectParams.terminal`
      - string
    * - PYO.USE_TCP_FAST_OPEN
      - :attr:`~ConnectParams.use_tcp_fast_open`
      - boolean
    * - PYO.WALLET_LOCATION
      - :attr:`~ConnectParams.wallet_location`
      - string

If a common or additional parameter is specified multiple times in a connect
string, then the last value of that parameter is considered as the value. For
example, if the ``sdu`` parameter is specified multiple times in the connect
string like this "sdu=5&sdu=10&pyo.sdu=15&sdu=20", then the value 20 is
considered as the value of the this parameter.

Note that the Connect String parameter names for the common and additional
parameters are not case-sensitive. The boolean values may use one of the
strings "on" or "off", "true" or "false", or "yes" or "no". The enumerated
values use the enumerated name and are converted to uppercase before they are
looked up in the enumeration. For example,
:data:`oracledb.AuthMode.SYSDBA <oracledb.AUTH_MODE_SYSDBA>` would be
specified as SYSDBA.

.. _connectionhook:

Connection Hook Functions
=========================

The :meth:`oracledb.register_protocol()` method registers a user hook function
that will be called internally by python-oracledb Thin mode prior to connection
or pool creation.  The hook function will be invoked when
:func:`oracledb.connect`, :func:`oracledb.create_pool`,
:meth:`oracledb.connect_async()`, or :meth:`oracledb.create_pool_async()` are
called with a ``dsn`` parameter value prefixed with a specified protocol.  Your
hook function is expected to construct valid connection details, which
python-oracledb will use to complete the connection or pool creation.

For example, the following hook function handles connection strings prefixed
with ``tcp://``.  When :func:`oracledb.connect()` is called, the sample hook is
invoked internally. It prints the parameters, and sets the connection
information in the ``params`` parameter (without passing the ``tcp://`` prefix
to :meth:`~ConnectParams.parse_connect_string()` otherwise recursion would
occur).  This modified ConnectParams object is used by python-oracledb to
establish the database connection:

.. code-block:: python

    def myhook(protocol, arg, params):
        print(f"In myhook: protocol={protocol} arg={arg}")
        params.parse_connect_string(arg)

    oracledb.register_protocol("tcp", myhook)

    connection = oracledb.connect(user="scott", password=userpwd,
                                  dsn="tcp://localhost/orclpdb")

    with connection.cursor() as cursor:
        for (r,) in cursor.execute("select user from dual"):
            print(r)

The output would be::

    In myhook: protocol=tcp arg=localhost/orclpdb
    SCOTT

The ``params`` :ref:`attributes <connparamsattr>` can be set with
:meth:`ConnectParams.parse_connect_string()`, as shown, or by using
:meth:`ConnectParams.set()`.

See :ref:`ldapconnections` for a fuller example.

Internal hook functions for the “tcp” and “tcps” protocols are pre-registered
but can be overridden, if needed.  If any other protocol has not been
registered, then connecting will result in an error.

Calling :meth:`~oracledb.register_protocol()` with the ``hook_function``
parameter set to None will result in a previously registered user function
being removed and the default behavior restored.

**Connection Hooks and parse_connect_string()**

A registered user hook function will also be invoked in python-oracledb Thin or
Thick modes when :meth:`ConnectParams.parse_connect_string()` is called with a
``connect_string`` parameter beginning with the registered protocol.  The hook
function ``params`` value will be the invoking ConnectParams instance that you
can update using :meth:`ConnectParams.set()` or
:meth:`ConnectParams.parse_connect_string()`.

For example, with the hook ``myhook`` shown previously, then the code:

.. code-block:: python

    cp = oracledb.ConnectParams()
    cp.set(port=1234)
    print(f"host is {cp.host}, port is {cp.port}, service name is {cp.service_name}")
    cp.parse_connect_string("tcp://localhost/orclpdb")
    print(f"host is {cp.host}, port is {cp.port}, service name is {cp.service_name}")

prints::

    host is None, port is 1234, service name is None
    In myhook: protocol=tcp arg=localhost/orclpdb
    host is localhost, port is 1234, service name is orclpdb

If you have an application that can run in either python-oracledb Thin or Thick
modes, and you want a registered connection hook function to be used in both
modes, your connection code can be like:

.. code-block:: python

    dsn = "tcp://localhost/orclpdb"

    cp = oracledb.ConnectParams()
    cp.parse_connect_string(dsn)
    connection = oracledb.connect(user="hr", password=userpwd, params=cp)

.. _registerpasswordtype:

Using oracledb.register_password_type()
---------------------------------------

The :meth:`oracledb.register_password_type()` method registers a user hook
function that will be called internally by python-oracledb prior to connection
or pool creation by :meth:`oracledb.connect()`, :meth:`oracledb.create_pool()`,
:meth:`oracledb.connect_async()`, or :meth:`oracledb.create_pool_async()`. If
the ``password``, ``newpassword``, or ``wallet_password`` parameters to those
methods are a dictionary containing the key "type", then the registered user
hook function will be invoked.  Your hook function is expected to accept the
dictionary and return the actual password string.

Below is an example of a hook function that handles passwords of type base64.
Note this specific hook function is already included and registered in
python-oracledb:

.. code-block:: python

    def mypasswordhook(args):
        return base64.b64decode(args["value"].encode()).decode()

    oracledb.register_password_type("base64", mypasswordhook)

When :meth:`oracledb.connect()` is called as shown below, the sample hook is
invoked internally. It decodes the base64-encoded string in the key "value" and
returns the password which is then used by python-oracledb to establish a
connection to the database:

.. code-block:: python

    connection = oracledb.connect(user="scott",
                                  password=dict(type="base64", value="dGlnZXI="),
                                  dsn="localhost/orclpdb")

Calling :meth:`~oracledb.register_password_type()` with the
``hook_function`` parameter set to None will result in a previously
registered user function being removed and the default behavior restored.

.. _ldapconnections:

LDAP Directory Naming
=====================

Directory Naming centralizes the network names and addresses used for
connections in a single place. More details can be found in `Configuring Oracle
Database Clients for OID and OUD Directory Naming
<https://www.oracle.com/a/otn/docs/database/oracle-net-oud-oid-directory-naming.pdf>`__
and `Configuring Oracle Database Clients for Microsoft Active Directory Naming
<https://www.oracle.com/a/otn/docs/database/oracle-net-active-directory-naming.pdf>`__.

**Thick Mode**

Once a directory server is configured, python-oracledb Thick mode applications
can use the desired LDAP alias as the connection DSN.

Oracle Client 23ai introduced support for LDAP URLs to be used as connection
strings. This syntax removes the need for external ``ldap.ora`` and
``sqlnet.ora`` files.  See the technical brief `Oracle Client 23ai LDAP URL
Syntax <https://www.oracle.com/a/otn/docs/database/oracle-net-23ai-ldap-url.
pdf>`__.  For example, python-oracledb Thick mode applications using Oracle
Client 23ai could connect using:

.. code-block:: python

    ldapurl = "ldaps://ldapserver.example.com/cn=orcl,cn=OracleContext,dc=example,dc=com"
    connection = oracledb.connect(user="scott", password=pw, dsn=ldapurl)

**Thin Mode**

To use LDAP in python-oracledb Thin mode, specify an LDAP URL as the DSN and
call :meth:`oracledb.register_protocol()` to register your own user
:ref:`connection hook function <connectionhook>` that gets the connect
string from your LDAP server.

For example:

.. code-block:: python

    import ldap3
    import re

    # Get the Oracle Database connection string from an LDAP server when
    # connection calls use an LDAP URL.
    # In this example, "protocol"' will have the value "ldap", and "arg" will
    # be "ldapserver/dbname,cn=OracleContext,dc=dom,dc=com"

    def ldap_hook(protocol, arg, params):
        pattern = r"^(.+)\/(.+)\,(cn=OracleContext.*)$"
        match = re.match(pattern, arg)
        ldap_server, db, ora_context = match.groups()

        server = ldap3.Server(ldap_server)
        conn = ldap3.Connection(server)
        conn.bind()
        conn.search(ora_context, f"(cn={db})", attributes=['orclNetDescString'])
        connect_string = conn.entries[0].orclNetDescString.value
        params.parse_connect_string(connect_string)

    oracledb.register_protocol("ldap", ldap_hook)

    connection = oracledb.connect(user="hr" password=userpwd,
                 dsn="ldap://ldapserver/dbname,cn=OracleContext,dc=dom,dc=com")

You can modify or extend this as needed, for example to use an LDAP module that
satisfies your business and security requirements, or to cache the response
from the LDAP server.

.. _appcontext:

Connection Metadata and Application Contexts
============================================

During connection you can set additional metadata properties that can be
accessed in the database for tracing and for enforcing fine-grained data
access, for example with Oracle Virtual Private Database policies. Values may
appear in logs and audit trails.

**End-to-End Tracing Attributes**

The connection attributes :attr:`Connection.client_identifier`,
:attr:`Connection.clientinfo`, :attr:`Connection.dbop`,
:attr:`Connection.module`, and :attr:`Connection.action` set metadata about the
connection.

It is recommended to always set at least :attr:`~Connection.client_identifier`,
:attr:`~Connection.module`, and :attr:`~Connection.action` for all applications
because their availability in the database can greatly aid future
troubleshooting.

See :ref:`endtoendtracing` for more information.

**Application Contexts**

An application context stores user identification that can enable or prevent a
user from accessing data in the database.  See the Oracle Database
documentation `About Application Contexts <https://www.oracle.com/pls/topic/
lookup?ctx=dblatest&id=GUID-6745DB10-F540-45D7-9761-9E8F342F1435>`__.

A context has a namespace and a key-value pair. The namespace CLIENTCONTEXT is
reserved for use with client session-based application contexts. Contexts are
set during connection as an array of 3-tuple containing string values for the
namespace, key, and value.  For example:

.. code-block:: python

    myctx = [
        ("clientcontext", "loc_id", "1900")
    ]

    connection = oracledb.connect(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb",
                                  appcontext=myctx)

Context values set during connection can be directly queried in your
applications. For example:

.. code-block:: python

    with connection.cursor() as cursor:
        sql = """select * from locations
                 where location_id = sys_context('clientcontext', 'loc_id')"""
        for r in cursor.execute(sql):
            print(r)

This will print::

    (1900, '6092 Boxwood St', 'YSW 9T2', 'Whitehorse', 'Yukon', 'CA')

Multiple context values can be set when connecting. For example:

.. code-block:: python

    myctx = [
        ("clientcontext", "loc_id", "1900"),
        ("clientcontext", "my_world", "earth"),
    ]

    connection = oracledb.connect(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb",
                                  appcontext=myctx)

    with connection.cursor() as cursor:
        sql = """select sys_context('clientcontext', 'loc_id'),
                        sys_context('clientcontext', 'my_world')
                 from dual"""
        for r in cursor.execute(sql):
            print(r)

will display::

    ('1900', 'earth')

You can use contexts to set up restrictive policies that are automatically
applied to any query executed. See Oracle Database documentation `Oracle
Virtual Private Database (VPD) <https://www.oracle.com/pls/topic/lookup?ctx=
dblatest&id=GUID-06022729-9210-4895-BF04-6177713C65A7>`__.

.. _connpooling:

Connection Pooling
==================

Python-oracledb's connection pooling lets applications create and maintain a
pool of open connections to the database.  Connection pooling is available in
both Thin and :ref:`Thick <enablingthick>` modes.  Connection pooling is
important for performance and scalability when applications need to handle a
large number of users who do database work for short periods of time but have
relatively long periods when the connections are not needed.  The high
availability features of pools also make small pools useful for applications
that want a few connections available for infrequent use and requires them to
be immediately usable when acquired.  Applications that would benefit from
connection pooling but are too difficult to modify from the use of
:ref:`standalone connections <standaloneconnection>` can take advantage of
:ref:`implicitconnpool`.

In python-oracledb Thick mode, the pool implementation uses Oracle's `session
pool technology <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-F9662FFB-EAEF-495C-96FC-49C6D1D9625C>`__ which supports additional
Oracle Database features, for example some advanced :ref:`high availability
<highavailability>` features.

.. note::

    Python-oracledb connection pools must be created, used and closed within
    the same process. Sharing pools or connections across processes has
    unpredictable behavior.

    Using connection pools in multi-threaded architectures is supported.

    Multi-process architectures that cannot be converted to threading may get
    some benefit from :ref:`drcp`.


Creating a Connection Pool
--------------------------

A connection pool is created by calling :meth:`oracledb.create_pool()`.
Various pool options can be specified as described in
:meth:`~oracledb.create_pool()` and detailed below.

For example, to create a pool that initially contains one connection but
can grow up to five connections:

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb",
                                min=1, max=5, increment=1)

Getting Connections from a Pool
+++++++++++++++++++++++++++++++

After a pool has been created, your application can get a connection from
it by calling :meth:`ConnectionPool.acquire()`:

.. code-block:: python

    connection = pool.acquire()

These connections can be used in the same way that :ref:`standaloneconnection`
are used.

By default, :meth:`~ConnectionPool.acquire()` calls wait for a connection
to be available before returning to the application.  A connection will be
available if the pool currently has idle connections, when another user
returns a connection to the pool, or after the pool grows.  Waiting allows
applications to be resilient to temporary spikes in connection load.  Users
may have to wait a brief time to get a connection but will not experience
connection failures.

You can change the behavior of :meth:`~ConnectionPool.acquire()` by setting the
``getmode`` option during pool creation.  For example, the option can be
set so that if all the connections are currently in use by the application, any
additional :meth:`~ConnectionPool.acquire()` call will return an error
immediately.

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb",
                                min=2, max=5, increment=1,
                                getmode=oracledb.POOL_GETMODE_NOWAIT)

Note that when using this option value in Thick mode with Oracle Client
libraries 12.2 or earlier, the :meth:`~ConnectionPool.acquire()` call will
still wait if the pool can grow.  However, you will get an error immediately if
the pool is at its maximum size.  With newer Oracle Client libraries and with
Thin mode, an error will be returned if the pool has to, or cannot, grow.

Returning Connections to a Pool
+++++++++++++++++++++++++++++++

When your application has finished performing all required database operations,
the pooled connection should be released back to the pool to make it available
for other users. For example, you can use a Python `context manager
<https://docs.python.org/3/library/stdtypes.html#context-manager-types>`__
``with`` block which lets pooled connections be closed implicitly at the end of
scope and cleans up dependent resources:

.. code-block:: python

    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            for result in cursor.execute("select * from mytab"):
                print(result)

Alternatively, you can explicitly return connections with
:meth:`ConnectionPool.release()` or :meth:`Connection.close()`, however you may
also need to close other resources first.

If you need to force a connection to be closed and its associated database
server process to be released, use :meth:`ConnectionPool.drop()`:

.. code-block:: python

    with pool.acquire() as connection:

        . . .

        pool.drop(connection)

Closing a Connection Pool
+++++++++++++++++++++++++

At application shutdown, the connection pool can be completely closed using
:meth:`ConnectionPool.close()`:

.. code-block:: python

    pool.close()

To force immediate pool termination when connections are still in use, execute:

.. code-block:: python

    pool.close(force=True)

See `connection_pool.py <https://github.com/oracle/python-oracledb/tree/main/
samples/connection_pool.py>`__ for a runnable example of connection pooling.

.. _connpoolcache:

Using the Connection Pool Cache
-------------------------------

When your application architecture makes it difficult to pass a
:ref:`ConnectionPool object <connpool>` between your code layers, you can use
the python-oracledb connection pool cache. This lets you store and retrieve
pools by name.

**Adding a pool to the python-oracledb connection pool cache**

To use the python-oracledb pool cache, specify the ``pool_alias`` parameter
when you create a pool during application initialization. Its value should be a
user-chosen string. For example:

.. code-block:: python

    import oracledb

    NAME = "my_pool"

    oracledb.create_pool(
        user="hr",
        password=userpwd,
        dsn="dbhost.example.com/orclpdb",
        pool_alias=NAME
    )

This creates a pool and stores it in the cache under the name "my_pool". The
application does not need to store or manage the reference to the pool so the
:meth:`~oracledb.create_pool()` return value is not saved.

If a pool already exists with the name "my_pool", the following error will
be raised::

    DPY-2055: connection pool with name "my_pool" already exists

**Getting a connection from a cached pool**

Applications can get a connection from a cached pool by passing its name
directly to :meth:`oracledb.connect()`:

.. code-block:: python

    import oracledb

    NAME = "my_pool"

    connection = oracledb.connect(pool_alias=NAME)

This is equivalent to calling :meth:`ConnectionPool.acquire()`. You can pass
additional parameters to :meth:`~oracledb.connect()` that are allowed for
:meth:`~ConnectionPool.acquire()`. For example, with a :ref:`heterogeneous
<connpooltypes>` pool you can pass the username and password:

.. code-block:: python

    import oracledb

    NAME = "my_pool"

    connection = oracledb.connect(pool_alias=NAME, user="toto", password=pw)

If there is no pool named ``my_pool`` in the cache, you will get the following
error::

    DPY-2054: connection pool with name "my_pool" does not exist

You cannot pass ``pool_alias`` and the deprecated ``pool`` parameter together
to :meth:`oracledb.connect()` or :meth:`oracledb.connect_async()`. If you do,
the following error is raised::

    DPY-2014: "pool_alias" and "pool" cannot be specified together

**Getting a pool from the connection pool cache**

You can use :meth:`oracledb.get_pool()` to retrieve a pool and then access it
directly:

.. code-block:: python

    import oracledb

    NAME = "my_pool"

    pool = oracledb.get_pool(NAME)
    connection = pool.acquire()

This allows any connection pool :ref:`method <connpoolmethods>` or
:ref:`attribute <connpoolattr>` from a cached pool to be used, as normal.

If there is no pool named ``my_pool`` in the cache, then
:meth:`~oracledb.get_pool()` will return None.

**Removing a pool from the cache**

A pool is automatically removed from the cache when the pool is closed:

.. code-block:: python

    import oracledb

    NAME = "my_pool"

    pool = oracledb.get_pool(NAME)
    pool.close()

.. _connpoolsize:

Connection Pool Sizing
----------------------

The Oracle Real-World Performance Group's recommendation is to use fixed size
connection pools.  The values of ``min`` and ``max`` should be the same.  When
using older versions of Oracle Client libraries the ``increment`` parameter
will need to be zero (which is internally treated as a value of one), but
otherwise you may prefer a larger size since this will affect how the
connection pool is re-established after, for example, a network dropout
invalidates all connections.

Fixed size pools avoid connection storms on the database which can decrease
throughput.  See `Guideline for Preventing Connection Storms: Use Static Pools
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-7DFBA826-7CC0-
4D16-B19C-31D168069B54>`__, which contains more details about sizing of pools.
Having a fixed size will also guarantee that the database can handle the upper
pool size.  For example, if a dynamically sized pool needs to grow but the
database resources are limited, then :meth:`ConnectionPool.acquire()` may
return errors such as `ORA-28547 <https://docs.oracle.com/error-help/db/ora-
28547/>`__.  With a fixed pool size, this class of error will occur when the
pool is created, allowing you to change the pool size or reconfigure the
database before users access the application.  With a dynamically growing pool,
the error may occur much later while the application is in use.

The Real-World Performance Group also recommends keeping pool sizes small
because they often can perform better than larger pools. The pool attributes
should be adjusted to handle the desired workload within the bounds of
available resources in python-oracledb and the database.

Connection Pool Growth
++++++++++++++++++++++

At pool creation, ``min`` connections are established to the database.  When a
pool needs to grow, new connections are created automatically limited by the
``max`` size.  The pool ``max`` size restricts the number of application users
that can do work in parallel on the database.

The number of connections opened by a pool can shown with the attribute.
:attr:`ConnectionPool.opened`.  The number of connections the application has
obtained with :meth:`~ConnectionPool.acquire()` can be shown with
:attr:`ConnectionPool.busy`.  The difference in values is the number of
connections unused or 'idle' in the pool.  These idle connections may be
candidates for the pool to close, depending on the pool configuration.

Pool growth is normally initiated when :meth:`~ConnectionPool.acquire()` is
called and there are no idle connections in the pool that can be returned to
the application.  The number of new connections created internally will be the
value of the :meth:`~oracledb.create_pool()` parameter ``increment``.

Depending on whether Thin or Thick mode is used and on the pool creation
``getmode`` value that is set, any :meth:`~ConnectionPool.acquire()` call that
initiates pool growth may wait until all ``increment`` new connections are
internally opened.  However, in this case the cost is amortized because later
:meth:`~ConnectionPool.acquire()` calls may not have to wait and can
immediately return an available connection.  Some users set larger
``increment`` values even for fixed-size pools because it can help a pool
re-establish itself if all connections become invalid, for example after a
network dropout.  In the common case of Thin mode with the default ``getmode``
of ``POOL_GETMODE_WAIT``, any :meth:`~ConnectionPool.acquire()` call that
initiates pool growth will return after the first new connection is created,
regardless of how big ``increment`` is.  The pool will then continue to
re-establish connections in a background thread.

A connection pool can shrink back to its minimum size ``min`` when connections
opened by the pool are not used by the application. This frees up database
resources while allowing pools to retain open connections for active users. If
there are more than ``min`` connections open, and connections are idle in the
pool (i.e. not currently acquired by the application) and unused for longer
than the pool creation attribute ``timeout`` value, then they will be closed.
The check occurs every ``timeout`` interval and hence in the worst case it may
take twice the ``timeout`` time to close the idle connections. The default
``timeout`` is *0* seconds signifying an infinite time and meaning idle
connections will never be closed.

The pool creation parameter ``max_lifetime_session`` also allows pools to
shrink. This parameter bounds the total length of time that a connection can
exist starting from the time that it was created in the pool. It is mostly used
for defensive programming to mitigate against unforeseeable problems that may
occur with connections. If a connection was created ``max_lifetime_session`` or
longer seconds ago, then it will be a candidate for being closed. In the case
when ``timeout`` and ``max_lifetime_session`` are both set, the connection will
be terminated if either the idle timeout happens or the maximum lifetime
setting is exceeded. Note that when using python-oracledb in Thick mode with
Oracle Client libraries prior to 21c, pool shrinkage is only initiated when the
pool is accessed so pools in fully dormant applications will not shrink until
the application is next used. In Thick mode, Oracle Client libraries 12.1, or
later, are needed to use ``max_lifetime_session``.

For pools created with :ref:`external authentication <extauth>`, with
:ref:`homogeneous <connpooltypes>` set to False, or when using :ref:`drcp` (in
python-oracledb Thick mode), then the number of connections opened at pool
creation is zero even if a larger value is specified for ``min``.  Also, in
these cases the pool increment unit is always 1 regardless of the value of
``increment``.

.. _poolhealth:

Pool Connection Health
----------------------

Before :meth:`ConnectionPool.acquire()` returns, python-oracledb does a
lightweight check similar to :meth:`Connection.is_healthy()` to see if the
network transport for the selected connection is still open.  If it is not,
then :meth:`~ConnectionPool.acquire()` will clean up the connection and return
a different one.

This check will not detect cases such as where the database session has been
terminated by the DBA, or reached a database resource manager quota limit.  To
help in those cases, :meth:`~ConnectionPool.acquire()` will also do a full
:ref:`round-trip <roundtrips>` database ping similar to
:meth:`Connection.ping()` when it is about to return a connection that was idle
in the pool (i.e. not acquired by the application) for
:data:`ConnectionPool.ping_interval` seconds.  If the ping fails, the
connection will be discarded and another one obtained before
:meth:`~ConnectionPool.acquire()` returns to the application.  The
``ping_timeout`` parameter to :meth:`oracledb.create_pool()` limits the amount
of time that any internal ping is allowed to take. If it is exceeded, perhaps
due to a network hang, the connection is considered unusable and a different
connection is returned to the application.

Because this full ping is time based and may not occur for each
:meth:`~ConnectionPool.acquire()`, the application may still get an unusable
connection.  Also, network timeouts and session termination may occur between
the calls to :meth:`~ConnectionPool.acquire()` and :meth:`Cursor.execute()`.
To handle these cases, applications need to check for errors after each
:meth:`~Cursor.execute()` and make application-specific decisions about
retrying work if there was a connection failure.  When using python-oracledb in
Thick mode, Oracle Database features like :ref:`Application Continuity
<highavailability>` can do this automatically in some cases.

You can explicitly initiate a full round-trip ping at any time with
:meth:`Connection.ping()` to check connection liveness but the overuse will
impact performance and scalability.  To avoid pings hanging due to network
errors, use :attr:`Connection.call_timeout` to limit the amount of time
:meth:`~Connection.ping()` is allowed to take.

The :meth:`Connection.is_healthy()` method is an alternative to
:meth:`Connection.ping()`.  It has lower overheads and may suit some uses, but
it does not perform a full connection check.

If the ``getmode`` parameter in :meth:`oracledb.create_pool()` is set to
:data:`oracledb.POOL_GETMODE_TIMEDWAIT`, then the maxium amount of time an
:meth:`~ConnectionPool.acquire()` call will wait to get a connection from the
pool is limited by the value of the :data:`ConnectionPool.wait_timeout`
parameter.  A call that cannot be immediately satisfied will wait no longer
than ``wait_timeout`` regardless of the value of ``ping_timeout``.

Connection pool health can be impacted by :ref:`firewalls <hanetwork>`,
`resource managers <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
GUID-2BEF5482-CF97-4A85-BD90-9195E41E74EF>`__ or user profile `IDLE_TIME
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-ABC7AE4D-64A8-
4EA9-857D-BEF7300B64C3>`__ values. For best efficiency, ensure these do not
expire idle sessions since this will require connections to be recreated which
will impact performance and scalability.

A pool's internal connection re-establishment after lightweight and full pings
can mask performance-impacting configuration issues such as firewalls
terminating connections.  You should monitor `AWR <https://www.oracle.com/pls/
topic/lookup?ctx=dblatest&id=GUID-56AEF38E-9400-427B-A818-EDEC145F7ACD>`__
reports for an unexpectedly large connection rate.

.. _poolreconfiguration:

Connection Pool Reconfiguration
-------------------------------

Some pool settings can be changed dynamically with
:meth:`ConnectionPool.reconfigure()`.  This allows the pool size and other
attributes to be changed during application runtime without needing to restart
the pool or application.

For example a pool's size can be changed like:

.. code-block:: python

    pool.reconfigure(min=10, max=10, increment=0)

After any size change has been processed, reconfiguration on the other
parameters is done sequentially. If an error such as an invalid value occurs
when changing one attribute, then an exception will be generated but any already
changed attributes will retain their new values.

During reconfiguration of a pool's size, the behavior of
:meth:`ConnectionPool.acquire()` depends on the pool creation ``getmode`` value
in effect when :meth:`~ConnectionPool.acquire()` is called, see
:meth:`ConnectionPool.reconfigure()`.  Closing connections or closing the pool
will wait until after pool reconfiguration is complete.

Calling ``reconfigure()`` is the only way to change a pool's ``min``, ``max``
and ``increment`` values.  Other attributes such as
:data:`~ConnectionPool.wait_timeout` can be passed to ``reconfigure()`` or they
can be set directly, for example:

.. code-block:: python

    pool.wait_timeout = 1000

.. _sessioncallback:

Session Callbacks for Setting Pooled Connection State
-----------------------------------------------------

Applications can set "session" state in each connection.  Examples of session
state are :ref:`NLS globalization <globalization>` settings from ``ALTER
SESSION`` statements.  Pooled connections will retain their session state after
they have been released back to the pool.  However, because pools can grow or
connections in the pool can be recreated, there is no guarantee a subsequent
:meth:`~ConnectionPool.acquire()` call will return a database connection that
has any particular state.

The :meth:`~oracledb.create_pool()` parameter ``session_callback`` enables
efficient setting of session state so that connections have a known session
state, without requiring that state to be explicitly set after every
:meth:`~ConnectionPool.acquire()` call.  The callback is internally invoked
when :meth:`~ConnectionPool.acquire()` is called and runs first.

The session callback can be a Python function or a PL/SQL procedure.

Connections can also be tagged when they are released back to the pool.  The
tag is a user-defined string that represents the session state of the
connection.  When acquiring connections, a particular tag can be requested.  If
a connection with that tag is available, it will be returned.  If not, then
another session will be returned.  By comparing the actual and requested tags,
applications can determine what exact state a session has, and make any
necessary changes.

Connection tagging and PL/SQL callbacks are only available in python-oracledb
Thick mode.  Python callbacks can be used in python-oracledb Thin and Thick
modes.

There are three common scenarios for ``session_callback``:

- When all connections in the pool should have the same state, use a
  Python callback without tagging.

- When connections in the pool require different state for different users, use
  a Python callback with tagging.

- With :ref:`drcp`, use a PL/SQL callback with tagging.

Python Callback
+++++++++++++++

If the ``session_callback`` parameter is a Python procedure, it will be called
whenever :meth:`~ConnectionPool.acquire()` will return a newly created database
connection that has not been used before.  It is also called when connection
tagging is being used and the requested tag is not identical to the tag in the
connection returned by the pool.

An example is:

.. code-block:: python

    # Set the NLS_DATE_FORMAT for a session
    def init_session(connection, requested_tag):
        with connection.cursor() as cursor:
            cursor.execute("alter session set nls_date_format = 'YYYY-MM-DD HH24:MI'")

    # Create the pool with session callback defined
    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="localhost/orclpdb",
                                session_callback=init_session)

    # Acquire a connection from the pool (will always have the new date format)
    connection = pool.acquire()

If needed, the ``init_session()`` procedure is called internally before
:meth:`~ConnectionPool.acquire()` returns.  It will not be called when
previously used connections are returned from the pool.  This means that the
ALTER SESSION does not need to be executed after every
:meth:`~ConnectionPool.acquire()` call.  This improves performance and
scalability.

In this example tagging was not being used, so the ``requested_tag`` parameter
is ignored.

Note that if you need to execute multiple SQL statements in the callback, use an
anonymous PL/SQL block to save :ref:`round-trips <roundtrips>` of repeated
``execute()`` calls.  With ALTER SESSION, pass multiple settings in the one
statement:

.. code-block:: python

    cursor.execute("""
            begin
                execute immediate
                        'alter session set nls_date_format = ''YYYY-MM-DD''
                                           nls_language = AMERICAN';
                -- other SQL statements could be put here
            end;""")

.. _conntagging:

Connection Tagging
++++++++++++++++++

Connection tagging is used when connections in a pool should have differing
session states.  In order to retrieve a connection with a desired state, the
``tag`` attribute in :meth:`~ConnectionPool.acquire()` needs to be set.

.. note::

    Connection tagging is only supported in the python-oracledb Thick mode. See
    :ref:`enablingthick` .

When python-oracledb is using Oracle Client libraries 12.2 or later, then
python-oracledb uses 'multi-property tags' and the tag string must be of the
form of one or more "name=value" pairs separated by a semi-colon, for example
``"loc=uk;lang=cy"``.

When a connection is requested with a given tag, and a connection with that tag
is not present in the pool, then a new connection, or an existing connection
with cleaned session state, will be chosen by the pool and the session callback
procedure will be invoked.  The callback can then set desired session state and
update the connection's tag.  However, if the ``matchanytag`` parameter of
:meth:`~ConnectionPool.acquire()` is True, then any other tagged connection may
be chosen by the pool and the callback procedure should parse the actual and
requested tags to determine which bits of session state should be reset.

The example below demonstrates connection tagging:

.. code-block:: python

    def init_session(connection, requested_tag):
        if requested_tag == "NLS_DATE_FORMAT=SIMPLE":
            sql = "ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD'"
        elif requested_tag == "NLS_DATE_FORMAT=FULL":
            sql = "ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI'"
        cursor = connection.cursor()
        cursor.execute(sql)
        connection.tag = requested_tag

    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="orclpdb",
                                 session_callback=init_session)

    # Two connections with different session state:
    connection1 = pool.acquire(tag="NLS_DATE_FORMAT=SIMPLE")
    connection2 = pool.acquire(tag="NLS_DATE_FORMAT=FULL")

See `session_callback.py
<https://github.com/oracle/python-oracledb/tree/main/
samples/session_callback.py>`__ for an example.

PL/SQL Callback
+++++++++++++++

.. note::

    PL/SQL Callbacks are only supported in the python-oracledb Thick mode. See
    :ref:`enablingthick`.

When python-oracledb uses Oracle Client 12.2 or later, the session callback can
also be the name of a PL/SQL procedure.  A PL/SQL callback will be initiated
only when the tag currently associated with a connection does not match the tag
that is requested.  A PL/SQL callback is most useful when using :ref:`drcp`
because DRCP does not require a :ref:`round-trip <roundtrips>` to invoke a
PL/SQL session callback procedure.

The PL/SQL session callback should accept two VARCHAR2 arguments:

.. code-block:: sql

    PROCEDURE myPlsqlCallback (
        requestedTag IN  VARCHAR2,
        actualTag    IN  VARCHAR2
    );

The logic in this procedure can parse the actual tag in the session that has
been selected by the pool and compare it with the tag requested by the
application.  The procedure can then change any state required before the
connection is returned to the application from
:meth:`~ConnectionPool.acquire()`.

If the ``matchanytag`` attribute of :meth:`~ConnectionPool.acquire()` is
*True*, then a connection with any state may be chosen by the pool.

Oracle 'multi-property tags' must be used.  The tag string must be of the form
of one or more "name=value" pairs separated by a semi-colon, for example
``"loc=uk;lang=cy"``.

In python-oracledb set ``session_callback`` to the name of the PL/SQL
procedure. For example:

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd,
                                 dsn="dbhost.example.com/orclpdb:pooled",
                                 session_callback="MyPlsqlCallback")

    connection = pool.acquire(tag="NLS_DATE_FORMAT=SIMPLE",
                              # DRCP options, if you are using DRCP
                              cclass='MYCLASS',
                              purity=oracledb.PURITY_SELF)

See `session_callback_plsql.py
<https://github.com/oracle/python-oracledb/tree/main/
samples/session_callback_plsql.py>`__ for an example.

.. _connpooltypes:

Heterogeneous and Homogeneous Connection Pools
----------------------------------------------

**Homogeneous Pools**

By default, connection pools are 'homogeneous', meaning that all connections
use the same database credentials.  Both python-oracledb Thin and :ref:`Thick
<enablingthick>` modes support homogeneous pools.

**Heterogeneous Pools**

The python-oracledb Thick mode additionally supports Heterogeneous pools,
allowing different user names and passwords to be passed to each
:meth:`~ConnectionPool.acquire()` call.

To create an heterogeneous pool, set the :meth:`~oracledb.create_pool()`
parameter ``homogeneous`` to False:

.. code-block:: python

    pool = oracledb.create_pool(dsn="dbhost.example.com/orclpdb", homogeneous=False)
    connection = pool.acquire(user="hr", password=userpwd)

.. _usingpoolparams:

Using the PoolParams Builder Class
----------------------------------

The :ref:`PoolParams class <poolparam>` allows you to define connection and
pool parameters in a single place.  The :func:`oracledb.PoolParams()` function
returns a ``PoolParams`` object.  This is a subclass of the :ref:`ConnectParams
class <connparam>` with additional pool-specific attributes such as the pool
size.  A ``PoolParams`` object can be passed to
:func:`oracledb.create_pool()`. For example:

.. code-block:: python

    pp = oracledb.PoolParams(min=1, max=2, increment=1)
    pool = oracledb.create_pool(user="hr", password=userpw, dsn="dbhost.example.com/orclpdb",
                                params=pp)

The use of the PoolParams class is optional because you can pass the same
parameters directly to :func:`~oracledb.create_pool()`.  For example, the code
above is equivalent to:

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpw, dsn="dbhost.example.com/orclpdb",
                                min=1, max=2, increment=1)

Most PoolParams arguments are gettable as properties.  They may be set
individually using the ``set()`` method:

.. code-block:: python

    pp = oracledb.PoolParams()
    pp.set(min=5)
    print(pp.min) # 5

Some values such as the database host name, can be specified as
:func:`oracledb.create_pool()` parameters, as part of the connect string, and
in the ``params`` object.  If a ``dsn`` is passed, a connection string is
internally constructed from the individual parameters and ``params`` object
values, with the individual parameters having precedence. The precedence is
that values in any ``dsn`` parameter override values passed as individual
parameters, which themselves override values set in the ``params`` object.
Similar precedence rules also apply to other values.

.. _definepoolparams:

Defining PoolParams Parameters in a Connection String
-----------------------------------------------------

You can specify certain common parameters of the :ref:`PoolParams object
<poolparam>` directly in an :ref:`Easy Connect string <easyconnect>`. This can
be done by using the question mark symbol (?) to indicate the start of the
parameter-value pairs and the ampersand symbol (&) to delimit each
parameter-value pair. See :ref:`_common_parameters` for the list of common
parameters.

Also, you can specify additional parameters of the :ref:`PoolParams object
<poolparam>` directly in an :ref:`Easy Connect string <easyconnect>`. This can
be done by using the question mark symbol (?) to indicate the start of the
parameter-value pairs and the ampersand symbol (&) to delimit each
parameter-value pair. Additionally, you must define each parameter name with
the prefix "pyo.". For example:

.. code-block:: python

    pp = oracledb.PoolParams()
    pp.parse_connect_string("host.example.com:1522/orclpdb?pyo.max=10&pyo.increment=2")

Note that these parameters can only be added in Easy Connect strings and not in
:ref:`Connect Descriptors <conndescriptor>`.

The PoolParams parameters that can be set in a connection string with the
prefix "pyo."" are listed in the table below:

.. list-table-with-summary::
    :header-rows: 1
    :class: wy-table-responsive
    :align: center
    :widths: 10 10 10
    :summary: The first column displays the connect string parameter name. The second column displays the Python parameter name. The third column displays the type of the parameter.

    * - Connect String Parameter Name
      - Python Parameter Name
      - Type
    * - PYO.CCLASS
      - :attr:`ConnectParams.cclass`
      - string
    * - PYO.CONNECTION_ID_PREFIX
      - :attr:`ConnectParams.connection_id_prefix`
      - string
    * - PYO.DISABLE_OOB
      - :attr:`ConnectParams.disable_oob`
      - boolean
    * - PYO.DRIVER_NAME
      - :attr:`ConnectParams.driver_name`
      - string
    * - PYO.EDITION
      - :attr:`ConnectParams.edition`
      - string
    * - PYO.EVENTS
      - :attr:`ConnectParams.events`
      - boolean
    * - PYO.EXPIRE_TIME
      - :attr:`ConnectParams.expire_time`
      - integer
    * - PYO.EXTERNALAUTH
      - :attr:`ConnectParams.externalauth`
      - boolean
    * - PYO.GETMODE
      - :attr:`PoolParams.getmode`
      - oracledb.PoolGetMode
    * - PYO.HOMOGENEOUS
      - :attr:`PoolParams.homogeneous`
      - boolean
    * - PYO.HTTPS_PROXY
      - :attr:`ConnectParams.https_proxy`
      - string
    * - PYO.HTTPS_PROXY_PORT
      - :attr:`ConnectParams.https_proxy_port`
      - integer
    * - PYO.INCREMENT
      - :attr:`PoolParams.increment`
      - integer
    * - PYO.MACHINE
      - :attr:`ConnectParams.machine`
      - string
    * - PYO.MAX
      - :attr:`PoolParams.max`
      - integer
    * - PYO.MAX_LIFETIME_SESSION
      - :attr:`PoolParams.max_lifetime_session`
      - integer
    * - PYO.MAX_SESSIONS_PER_SHARD
      - :attr:`PoolParams.max_sessions_per_shard`
      - integer
    * - PYO.MIN
      - :attr:`PoolParams.min`
      - integer
    * - PYO.MODE
      - :attr:`ConnectParams.mode`
      - oracledb.AuthMode
    * - PYO.OSUSER
      - :attr:`ConnectParams.osuser`
      - string
    * - PYO_PING_INTERVAL
      - :attr:`PoolParams.ping_interval`
      - integer
    * - PYO.PING_TIMEOUT
      - :attr:`PoolParams.ping_timeout`
      - integer
    * - PYO.POOL_BOUNDARY
      - :attr:`ConnectParams.pool_boundary`
      - string
    * - PYO.PROGRAM
      - :attr:`ConnectParams.program`
      - string
    * - PYO.PURITY
      - :attr:`ConnectParams.purity`
      - oracledb.Purity
    * - PYO.RETRY_COUNT
      - :attr:`ConnectParams.retry_count`
      - integer
    * - PYO.RETRY_DELAY
      - :attr:`ConnectParams.retry_delay`
      - integer
    * - PYO.SDU
      - :attr:`ConnectParams.sdu`
      - integer
    * - PYO.SODA_METADATA_CACHE
      - :attr:`PoolParams.soda_metadata_cache`
      - boolean
    * - PYO.SSL_SERVER_CERT_DN
      - :attr:`ConnectParams.ssl_server_cert_dn`
      - string
    * - PYO.SSL_SERVER_DN_MATCH
      - :attr:`ConnectParams.ssl_server_dn_match`
      - boolean
    * - PYO.STMTCACHESIZE
      - :attr:`ConnectParams.stmtcachesize`
      - integer
    * - PYO.TCP_CONNECT_TIMEOUT
      - :attr:`ConnectParams.tcp_connect_timeout`
      - integer
    * - PYO.TERMINAL
      - :attr:`ConnectParams.terminal`
      - string
    * - PYO.TIMEOUT
      - :attr:`PoolParams.timeout`
      - integer
    * - PYO.USE_TCP_FAST_OPEN
      - :attr:`ConnectParams.use_tcp_fast_open`
      - boolean
    * - PYO.WAIT_TIMEOUT
      - :attr:`PoolParams.wait_timeout`
      - integer
    * - PYO.WALLET_LOCATION
      - :attr:`ConnectParams.wallet_location`
      - string

If a common or additional parameter is specified multiple times in a connect
string, then the last value of that parameter is considered as the value. For
example, if the ``sdu`` parameter is specified multiple times in the connect
string like this "sdu=5&sdu=10&pyo.sdu=15&sdu=20", then the value 20 is
considered as the value of the this parameter.

Note that the Connect String parameter names for the common and additional
parameters are not case-sensitive. The boolean values may use one of the
strings "on" or "off", "true" or "false", or "yes" or "no". The enumerated
values use the enumerated name and are converted to uppercase before they are
looked up in the enumeration. For example,
:data:`oracledb.AuthMode.SYSDBA <oracledb.AUTH_MODE_SYSDBA>` would be
specified as SYSDBA.

.. _drcp:

Database Resident Connection Pooling (DRCP)
===========================================

`Database Resident Connection Pooling (DRCP)
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-015CA8C1-2386-4626-855D-CC546DDC1086>`__ enables database resource
sharing for applications which use a large number of connections that run in
multiple client processes or run on multiple middle-tier application servers.
By default, each connection from Python will use one database server process.
DRCP allows pooling of these server processes.  This reduces the amount of
memory required on the database host.  The DRCP pool can be shared by multiple
applications.

DRCP is useful for applications which share the same database credentials, have
similar session settings (for example date format settings or PL/SQL package
state), and where the application gets a database connection, works on it for a
relatively short duration, and then releases it.

For efficiency, it is recommended that DRCP connections should be used in
conjunction with python-oracledb's local :ref:`connection pool <connpooling>`.
Using DRCP with :ref:`standalone connections <standaloneconnection>` is not as
efficient but does allow the database to reuse database server processes which
can provide a performance benefit for applications that cannot use a local
connection pool. In this scenario, make sure to configure enough DRCP
authentication servers to handle the connection load.

Although applications can choose whether or not to use DRCP pooled connections
at runtime, care must be taken to configure the database appropriately for the
number of expected connections, and also to stop inadvertent use of non-DRCP
connections leading to a database server resource shortage. Conversely, avoid
using DRCP connections for long-running operations.

For more information about DRCP, see the technical brief `Extreme Oracle
Database Connection Scalability with Database Resident Connection Pooling
(DRCP) <https://www.oracle.com/docs/tech/drcp-technical-brief.pdf>`__, the user
documentation `Oracle Database Concepts Guide
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-531EEE8A-B00A-4C03-A2ED-D45D92B3F797>`__, and for DRCP Configuration
see `Oracle Database Administrator's Guide
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-82FF6896-F57E-41CF-89F7-755F3BC9C924>`__.

Using DRCP with python-oracledb applications involves the following steps:

1. Configuring and enabling DRCP in the database
2. Configuring the application to use a DRCP connection
3. Deploying the application

Enabling DRCP in Oracle Database
--------------------------------

Every Oracle Database uses a single, default DRCP connection pool.  From Oracle
Database 21c, each pluggable database can optionally have its own pool.  Note
that DRCP is already enabled in Oracle Autonomous Database and pool management
is different to the steps below.

DRCP pools can be configured and administered by a DBA using the
``DBMS_CONNECTION_POOL`` package:

.. code-block:: sql

    EXECUTE DBMS_CONNECTION_POOL.CONFIGURE_POOL(
        pool_name => 'SYS_DEFAULT_CONNECTION_POOL',
        minsize => 4,
        maxsize => 40,
        incrsize => 2,
        session_cached_cursors => 20,
        inactivity_timeout => 300,
        max_think_time => 600,
        max_use_session => 500000,
        max_lifetime_session => 86400)

Alternatively, the method ``DBMS_CONNECTION_POOL.ALTER_PARAM()`` can
set a single parameter:

.. code-block:: sql

    EXECUTE DBMS_CONNECTION_POOL.ALTER_PARAM(
        pool_name => 'SYS_DEFAULT_CONNECTION_POOL',
        param_name => 'MAX_THINK_TIME',
        param_value => '1200')

The ``inactivity_timeout`` setting terminates idle pooled servers, helping
optimize database resources.  To avoid pooled servers permanently being held
onto by a selfish Python script, the ``max_think_time`` parameter can be set.
The parameters ``num_cbrok`` and ``maxconn_cbrok`` can be used to distribute
the persistent connections from the clients across multiple brokers.  This may
be needed in cases where the operating system per-process descriptor limit is
small.  Some customers have found that having several connection brokers
improves performance.  The ``max_use_session`` and ``max_lifetime_session``
parameters help protect against any unforeseen problems affecting server
processes.  The default values will be suitable for most users.  See the
`Oracle DRCP documentation
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-015CA8C1-2386-4626-855D-CC546DDC1086>`__ for details on parameters.

In general, if pool parameters are changed, then the pool should be restarted.
Otherwise, server processes will continue to use old settings.

There is a ``DBMS_CONNECTION_POOL.RESTORE_DEFAULTS()`` procedure to
reset all values.

When DRCP is used with RAC, each database instance has its own connection
broker and pool of servers.  Each pool has the identical configuration.  For
example, all pools start with ``minsize`` server processes.  A single
DBMS_CONNECTION_POOL command will alter the pool of each instance at the same
time.  The pool needs to be started before connection requests begin.  The
command below does this by bringing up the broker, which registers itself with
the database listener:

.. code-block:: sql

    EXECUTE DBMS_CONNECTION_POOL.START_POOL()

Once enabled this way, the pool automatically restarts when the database
instance restarts, unless explicitly stopped with the
``DBMS_CONNECTION_POOL.STOP_POOL()`` command:

.. code-block:: sql

    EXECUTE DBMS_CONNECTION_POOL.STOP_POOL()

The pool cannot be stopped while connections are open.

Coding Applications to use DRCP
-------------------------------

To use DRCP, application connection establishment must request a DRCP pooled
server.  The best practice is also to specify a user-chosen connection class
name when creating a connection pool.  A 'purity' of the connection session
state can optionally be specified. See the Oracle Database documentation on
`benefiting from scalability <https://www.oracle.com/pls/topic/lookup?ctx=
dblatest&id=GUID-661BB906-74D2-4C5D-9C7E-2798F76501B3>`__ for more information
on purity and connection classes.

Note that when using DRCP with a python-oracledb local :ref:`connection pool
<connpooling>` in Thick mode, the local connection pool ``min`` value is
ignored and the pool will be created with zero connections.

**Requesting a Pooled Server**

To request a DRCP pooled server, you can:

- Use a specific connection string in :meth:`oracledb.create_pool()` or
  :meth:`oracledb.connect()`. For example with the
  :ref:`Easy Connect syntax <easyconnect>`:

  .. code-block:: python

        pool = oracledb.create_pool(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb:pooled",
                                    min=2, max=5, increment=1,
                                    cclass="MYAPP")

- Alternatively, add ``(SERVER=POOLED)`` to the :ref:`Connect Descriptor
  <conndescriptor>` such as used in an Oracle Network configuration file
  ``tnsnames.ora``::

    customerpool = (DESCRIPTION=(ADDRESS=(PROTOCOL=tcp)
              (HOST=dbhost.example.com)
              (PORT=1521))(CONNECT_DATA=(SERVICE_NAME=CUSTOMER)
              (SERVER=POOLED)))

- Another way to use a DRCP pooled server is to set the ``server_type``
  parameter during standalone connection creation or python-oracledb
  connection pool creation.  For example:

  .. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb",
                                min=2, max=5, increment=1,
                                server_type="pooled",
                                cclass="MYAPP")


**DRCP Connection Class Names**

The best practice is to specify a ``cclass`` class name when creating a
python-oracledb connection pool.  This user-chosen name provides some
partitioning of DRCP session memory so reuse is limited to similar
applications.  It provides maximum pool sharing if multiple application
processes are started.  A class name also allows better DRCP usage tracking in
the database.  In the database monitoring views, the class name shown will be
the value specified in the application prefixed with the user name.

If ``cclass`` was not specified during pool creation, then the python-oracledb
Thin mode generates a unique connection class with the prefix "DPY" while the
Thick mode generates a unique connection class with the prefix "OCI".

To create a connection pool requesting a DRCP pooled server and specifying a
class name, you can call:

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb:pooled",
                                min=2, max=5, increment=1,
                                cclass="MYAPP")

Once the pool has been created, your application can get a connection from it
by calling:

.. code-block:: python

    connection = pool.acquire()

The python-oracledb connection pool size does not need to match the DRCP pool
size.  The limit on overall execution parallelism is determined by the DRCP
pool size.

Connection class names can also be passed to :meth:`~ConnectionPool.acquire()`,
if you want to use a connection with a different class:

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb:pooled",
                                min=2, max=5, increment=1,
                                cclass="MYAPP")

    connection = mypool.acquire(cclass="OTHERAPP")

If a pooled server of a requested class is not available, a server with new
session state is used.  If the DRCP pool cannot grow, a server with a different
class may be used and its session state cleared.

If ``cclass`` is not set, then the pooled server sessions will not be reused
optimally, and the DRCP statistic views may record large values for NUM_MISSES.

**DRCP Connection Purity**

DRCP allows the connection session memory to be reused or cleaned each time a
connection is acquired from the pool.  The pool or connection creation
``purity`` parameter can be one of ``PURITY_NEW``, ``PURITY_SELF``, or
``PURITY_DEFAULT``.  The value ``PURITY_SELF`` allows reuse of both the pooled
server process and session memory, giving maximum benefit from DRCP.  By
default, python-oracledb pooled connections use ``PURITY_SELF`` and standalone
connections use ``PURITY_NEW``.

To limit session sharing, you can explicitly require that new session memory be
allocated each time :meth:`~ConnectionPool.acquire()` is called:

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb:pooled",
                                min=2, max=5, increment=1,
                                cclass="MYAPP", purity=oracledb.PURITY_NEW)

**Setting the Connection Class and Purity in the Connection String**

Using python-oracledb Thin mode with Oracle Database 21c, or later, you can
specify the class and purity in the connection string itself.  This removes the
need to modify an existing application when you want to use DRCP:

.. code-block:: python

    dsn = "localhost/orclpdb:pooled?pool_connection_class=MYAPP&pool_purity=self"

For python-oracledb Thick mode, this syntax is supported if you are using
Oracle Database 21c (or later) and Oracle Client 19c (or later). However,
explicitly specifying the purity as *SELF* in this way may cause some unusable
connections in a python-oracledb Thick mode connection pool to not be
terminated.  In summary, if you cannot programmatically set the class name and
purity, or cannot use python-oracledb Thin mode, then avoid explicitly setting
the purity as a connection string parameter when using a python-oracledb
connection pooling in Thick mode.

**Closing Connections when using DRCP**

Similar to using a python-oracledb connection pool, Python scripts where
python-oracledb connections do not go out of scope quickly (which releases
them), or do not currently use :meth:`Connection.close()` or
:meth:`ConnectionPool.release()` should be examined to see if the connections
can be closed earlier.  This allows maximum reuse of DRCP pooled servers by
other users:

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb:pooled",
                                min=2, max=5, increment=1,
                                cclass="MYAPP")

    # Do some database operations
    connection = mypool.acquire()
    . . .
    connection.close();             # <- Add this to release the DRCP pooled server

    # Do lots of non-database work
    . . .

    # Do some more database operations
    connection = mypool.acquire()   # <- And get a new pooled server only when needed
    . . .
    connection.close();

See `drcp_pool.py
<https://github.com/oracle/python-oracledb/tree/main/samples/drcp_pool.py>`__
for a runnable example of DRCP.

.. _monitoringdrcp:

Monitoring DRCP
---------------

Data dictionary views are available to monitor the performance of DRCP.
Database administrators can check statistics such as the number of busy and
free servers, and the number of hits and misses in the pool against the total
number of requests from clients. The views include:

* DBA_CPOOL_INFO
* V$PROCESS
* V$SESSION
* V$CPOOL_STATS
* V$CPOOL_CC_STATS
* V$CPOOL_CONN_INFO

**DBA_CPOOL_INFO View**

DBA_CPOOL_INFO displays configuration information about the DRCP pool.  The
columns are equivalent to the ``dbms_connection_pool.configure_pool()``
settings described in the table of DRCP configuration options, with the
addition of a STATUS column.  The status is ``ACTIVE`` if the pool has been
started and ``INACTIVE`` otherwise.  Note that the pool name column is called
CONNECTION_POOL.  This example checks whether the pool has been started and
finds the maximum number of pooled servers::

    SQL> SELECT connection_pool, status, maxsize FROM dba_cpool_info;

    CONNECTION_POOL              STATUS        MAXSIZE
    ---------------------------- ---------- ----------
    SYS_DEFAULT_CONNECTION_POOL  ACTIVE             40

**V$PROCESS and V$SESSION Views**

The V$SESSION view shows information about the currently active DRCP
sessions.  It can also be joined with V$PROCESS through
``V$SESSION.PADDR = V$PROCESS.ADDR`` to correlate the views.

**V$CPOOL_STATS View**

The V$CPOOL_STATS view displays information about the DRCP statistics for
an instance.  The V$CPOOL_STATS view can be used to assess how efficient the
pool settings are.  This example query shows an application using the pool
effectively.  The low number of misses indicates that servers and sessions were
reused.  The wait count shows just over 1% of requests had to wait for a pooled
server to become available::

    NUM_REQUESTS   NUM_HITS NUM_MISSES  NUM_WAITS
    ------------ ---------- ---------- ----------
           10031      99990         40       1055

If ``cclass`` was set (allowing pooled servers and sessions to be
reused), then NUM_MISSES will be low.  If the pool maxsize is too small for
the connection load, then NUM_WAITS will be high.

**V$CPOOL_CC_STATS View**

The view V$CPOOL_CC_STATS displays information about the connection class
level statistics for the pool per instance::

    SQL> select cclass_name, num_requests, num_hits, num_misses
         from v$cpool_cc_stats;

    CCLASS_NAME                      NUM_REQUESTS   NUM_HITS NUM_MISSES
    -------------------------------- ------------ ---------- ----------
    HR.MYCLASS                             100031      99993         38


The class name columns shows the database user name appended with the
connection class name.

**V$CPOOL_CONN_INFO View**

The V$POOL_CONN_INFO view gives insight into client processes that are
connected to the connection broker, making it easier to monitor and trace
applications that are currently using pooled servers or are idle. This view was
introduced in Oracle 11gR2.

You can monitor the view V$CPOOL_CONN_INFO to, for example, identify
misconfigured machines that do not have the connection class set correctly.
This view maps the machine name to the class name.  In python-oracledb Thick
mode, the class name will be default to one like shown below::

    SQL> select cclass_name, machine from v$cpool_conn_info;

    CCLASS_NAME                             MACHINE
    --------------------------------------- ------------
    CJ.OCI:SP:wshbIFDtb7rgQwMyuYvodA        cjlinux

In this example, you would examine applications on ``cjlinux`` and make them
set ``cclass``.

When connecting to Oracle Autonomous Database on Shared Infrastructure (ADB-S),
the V$CPOOL_CONN_INFO view can be used to track the number of connection
hits and misses to show the pool efficiency.

.. _implicitconnpool:

Implicit Connection Pooling
===========================

`Implicit connection pooling <https://
www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-A9D74994-D81A-47BF-BAF2-
E4E1A354CA99>`__ is useful for applications that cause excess database server
load due to the number of :ref:`standalone connections <standaloneconnection>`
opened.  When these applications cannot be rewritten to use
:ref:`python-oracledb connection pooling <connpooling>`, then implicit
connection pooling may be an option to reduce the load on the database system.

Implicit connection pooling allows application connections to share pooled
servers in :ref:`DRCP <drcp>` or Oracle Connection Manager in Traffic Director
Mode's (CMAN-TDM) `Proxy Resident Connection Pooling (PRCP)
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-E0032017-03B1-
4F14-AF9B-BCC87C982DA8>`__.  Applications do not need to be modified.  The
feature is enabled by adding a ``pool_boundary`` parameter to the application's
:ref:`connection string <connstr>`.  Applications do not need to explicitly
acquire, or release, connections to be able use a DRCP or PRCP pool.

Implicit connection pooling is available in python-oracledb Thin and
:ref:`Thick <enablingthick>` modes.  It requires Oracle Database
23ai. Python-oracledb Thick mode additionally requires Oracle Client 23ai
libraries.

With implicit connection pooling, connections are internally acquired from the
DRCP or PRCP pool when they are actually used by the application to do database
work.  They are internally released back to pool when not in use.  This may
occur between the application's explicit :meth:`oracledb.connect()` call and
:meth:`Connection.close()` (or the application's equivalent connection release
at end-of-scope).  The internal connection release can be controlled by the
value of the ``pool_boundary`` connection string parameter, which can be
either:

- *statement*: If this boundary is specified, then the connection is released
  back to the DRCP or PRCP connection pool when the connection is implicitly
  stateless.  A connection is implicitly stateless when there are no active
  cursors in the connection (that is, all the rows of the cursors have been
  internally fetched), no active transactions, no temporary tables, and no
  temporary LOBs.

- *transaction*: If this boundary is specified, then the connection is released
  back to the DRCP or PRCP connection pool when either one of the methods
  :meth:`Connection.commit()` or :meth:`Connection.rollback()` are
  called. It is recommended to not set the :attr:`Connection.autocommit`
  attribute to *true* when using implicit connection pooling.  If you do set
  this attribute, then you will be unable to:

  - Fetch any data that requires multiple :ref:`round-trips <roundtrips>` to
    the database
  - Run queries that fetch :ref:`LOB <lobdata>` and :ref:`JSON <jsondatatype>`
    data

Inline with DRCP and PRCP best practices regarding session sharing across
differing applications, you should add a connection string
``pool_connection_class`` parameter, using the same value for all applications
that are alike.

The DRCP and PRCP "purity" used by Implicit Connection Pooling defaults to
SELF, which allows reuse of the server process session memory for best
performance. Adding the connection string parameter ``pool_purity=new`` will
change this and cause each use of a connection to recreate the session memory.

.. _useimplicitconnpool:

**Configuring Implicit Connection Pooling**

To use implicit connection pooling in python-oracledb with DRCP:

1. Enable DRCP in the database. For example in SQL*Plus::

       SQL> EXECUTE DBMS_CONNECTION_POOL.START_POOL()

2. Specify to use a pooled server in:

   - The ``dsn`` parameter of :meth:`oracledb.connect()` or
     :meth:`oracledb.create_pool()`. For example with the
     :ref:`Easy Connect syntax <easyconnect>`:

     .. code-block:: python

        cs = "dbhost.example.com/orclpdb:pooled"

        pool = oracledb.create_pool(user="hr", password=userpwd,
                                    dsn=cs,
                                    min=2, max=5, increment=1,
                                    cclass="MYAPP")

   - Or in the :ref:`Connect Descriptor <conndescriptor>` used in an Oracle
     Network configuration file such as :ref:`tnsnames.ora <optnetfiles>` by
     adding ``(SERVER=POOLED)``. For example::

        customerpool = (DESCRIPTION=(ADDRESS=(PROTOCOL=tcp)
              (HOST=dbhost.example.com)
              (PORT=1521))(CONNECT_DATA=(SERVICE_NAME=CUSTOMER)
              (SERVER=POOLED)))

   - Or in the ``server_type`` parameter during
     :meth:`standalone connection creation <oracledb.connect>`
     or :meth:`connection pool creation <oracledb.create_pool>`.  For example:

     .. code-block:: python

        pool = oracledb.create_pool(user="hr", password=userpwd,
                                    host="dbhost.example.com", service_name="orclpdb",
                                    min=2, max=5, increment=1, server_type="pooled",
                                    cclass="MYAPP")

3. Set the pool boundary to either *statement* or *transaction* in:

   - The :ref:`Easy Connect string <easyconnect>`. For example, to use the
     *statement* boundary::

        dsn = "localhost:1521/orclpdb:pooled?pool_boundary=statement"

   - Or the ``CONNECT_DATA`` section of the :ref:`Connect Descriptor
     <conndescriptor>`. For example, to use the *transaction* boundary::

        tnsalias = (DESCRIPTION=(ADDRESS=(PROTOCOL=tcp)(HOST=mymachine.example.com)
                    (PORT=1521))(CONNECT_DATA=(SERVICE_NAME=orcl)
                    (SERVER=POOLED)(POOL_BOUNDARY=TRANSACTION)))

   - Or the ``pool_boundary`` parameter in :meth:`oracledb.connect()` or
     :meth:`oracledb.create_pool()`

   .. note::

        Implicit connection pooling is not enabled if the application sets the
        ``pool_boundary`` attribute to *transaction* or *statement* but does
        not specify to use a pooled server.

4. Set the connection class in:

    - The :ref:`Easy Connect string <easyconnect>`. For example, to use a class
      name 'myapp'::

        dsn = "localhost:1521/orclpdb:pooled?pool_boundary=statement&pool_connection_class=myapp"

    - Or the ``CONNECT_DATA`` section of the :ref:`Connect Descriptor
      <conndescriptor>`. For example, to use a class name 'myapp'::

        tnsalias = (DESCRIPTION=(ADDRESS=(PROTOCOL=tcp)(HOST=mymachine.example.com)
                    (PORT=1521))(CONNECT_DATA=(SERVICE_NAME=orcl)
                    (SERVER=POOLED)(POOL_BOUNDARY=TRANSACTION)
                    (POOL_CONNECTION_CLASS=myapp)))

   Use the same connection class name for application processes of the same
   type where you want session memory to be reused for connections.

   The pool purity can also optionally be changed by adding ``POOL_PURITY=NEW``
   to the Easy Connect string or Connect Descriptor.

Similar steps can be used with PRCP.  For general information on PRCP, see the
technical brief `CMAN-TDM — An Oracle Database connection proxy for scalable
and highly available applications <https://download.oracle.com/
ocomdocs/global/CMAN_TDM_Oracle_DB_Connection_Proxy_for_scalable_apps.pdf>`__.

**Implicit Pooling Notes**

You should thoroughly test your application when using implicit connection
pooling to ensure that the internal reuse of database servers does not cause
any problems. For example, any session state such as the connection `session id
and serial number
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-9F0DCAEA-A67E
-4183-89E7-B1555DC591CE>`__ will vary throughout the lifetime of the
application connection because different servers may be used at different
times. Another example is when using a statement boundary of *transaction*. In
this scenario, any commit can invalidate open cursors.

It is recommended to use python-oracledb's local :ref:`connpooling` where
possible instead of implicit connection pooling.  This gives multi-user
applications more control over pooled server reuse.


.. _proxyauth:

Connecting Using Proxy Authentication
=====================================

Proxy authentication allows a user (the "session user") to connect to Oracle
Database using the credentials of a "proxy user".  Statements will run as the
session user.  Proxy authentication is generally used in three-tier applications
where one user owns the schema while multiple end-users access the data.  For
more information about proxy authentication, see the `Oracle documentation
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-D77D0D4A-7483-423A-9767-CBB5854A15CC>`__.

An alternative to using proxy users is to set
:attr:`Connection.client_identifier` after connecting and use its value in
statements and in the database, for example for :ref:`monitoring
<endtoendtracing>`.

The following proxy examples use these schemas.  The ``mysessionuser`` schema is
granted access to use the password of ``myproxyuser``:

.. code-block:: sql

    CREATE USER myproxyuser IDENTIFIED BY myproxyuserpw;
    GRANT CREATE SESSION TO myproxyuser;

    CREATE USER mysessionuser IDENTIFIED BY itdoesntmatter;
    GRANT CREATE SESSION TO mysessionuser;

    ALTER USER mysessionuser GRANT CONNECT THROUGH myproxyuser;

After connecting to the database, the following query can be used to show the
session and proxy users:

.. code-block:: sql

    SELECT SYS_CONTEXT('USERENV', 'PROXY_USER'),
           SYS_CONTEXT('USERENV', 'SESSION_USER')
    FROM DUAL;

Standalone connection examples:

.. code-block:: python

    # Basic Authentication without a proxy
    connection = oracledb.connect(user="myproxyuser", password="myproxyuserpw",
                                  dsn="dbhost.example.com/orclpdb")
    # PROXY_USER:   None
    # SESSION_USER: MYPROXYUSER

    # Basic Authentication with a proxy
    connection = oracledb.connect(user="myproxyuser[mysessionuser]", password="myproxyuserpw",
                                  dsn="dbhost.example.com/orclpdb")
    # PROXY_USER:   MYPROXYUSER
    # SESSION_USER: MYSESSIONUSER

Pooled connection examples:

.. code-block:: python

    # Basic Authentication without a proxy
    pool = oracledb.create_pool(user="myproxyuser", password="myproxyuserpw",
                                dsn="dbhost.example.com/orclpdb")
    connection = pool.acquire()
    # PROXY_USER:   None
    # SESSION_USER: MYPROXYUSER

    # Basic Authentication with proxy
    pool = oracledb.create_pool(user="myproxyuser[mysessionuser]", password="myproxyuserpw",
                                dsn="dbhost.example.com/orclpdb",
                                homogeneous=False)

    connection = pool.acquire()
    # PROXY_USER:   MYPROXYUSER
    # SESSION_USER: MYSESSIONUSER

Note the use of a :ref:`heterogeneous <connpooltypes>` pool in the example
above.  This is required in this scenario.

.. _extauth:

Connecting Using External Authentication
========================================

Instead of storing the database username and password in Python scripts or
environment variables, database access can be authenticated by an outside
system.  External Authentication allows applications to validate user access
with an external password store (such as an
:ref:`Oracle Wallet <extauthwithwallet>`), with the
:ref:`operating system <opsysauth>`, or with an external authentication
service.

.. note::

    Connecting to Oracle Database using external authentication is only
    supported in the python-oracledb Thick mode. See :ref:`enablingthick`.

.. _extauthwithwallet:

Using an Oracle Wallet for External Authentication
--------------------------------------------------

The following steps give an overview of using an Oracle Wallet.  Wallets should
be kept securely.  Wallets can be managed with `Oracle Wallet Manager
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-E3E16C82-E174-4814-98D5-EADF1BCB3C37>`__.

In this example the wallet is created for the ``myuser`` schema in the directory
``/home/oracle/wallet_dir``.  The ``mkstore`` command is available from a full
Oracle client or Oracle Database installation.  If you have been given wallet by
your DBA, skip to step 3.

1.  First create a new wallet as the ``oracle`` user::

        mkstore -wrl "/home/oracle/wallet_dir" -create

    This will prompt for a new password for the wallet.

2.  Create the entry for the database user name and password that are currently
    hardcoded in your Python scripts.  Use either of the methods shown below.
    They will prompt for the wallet password that was set in the first step.

    **Method 1 - Using an Easy Connect string**::

        mkstore -wrl "/home/oracle/wallet_dir" -createCredential dbhost.example.com/orclpdb myuser myuserpw

    **Method 2 - Using a connect name identifier**::

        mkstore -wrl "/home/oracle/wallet_dir" -createCredential mynetalias myuser myuserpw

    The alias key ``mynetalias`` immediately following the
    ``-createCredential`` option will be the connect name to be used in Python
    scripts.  If your application connects with multiple different database
    users, you could create a wallet entry with different connect names for
    each.

    You can see the newly created credential with::

        mkstore -wrl "/home/oracle/wallet_dir" -listCredential

3.  Skip this step if the wallet was created using an Easy Connect String.
    Otherwise, add an entry in :ref:`tnsnames.ora <optnetfiles>` for the connect
    name as follows::

        mynetalias =
            (DESCRIPTION =
                (ADDRESS = (PROTOCOL = TCP)(HOST = dbhost.example.com)(PORT = 1521))
                (CONNECT_DATA =
                    (SERVER = DEDICATED)
                    (SERVICE_NAME = orclpdb)
                )
            )

    The file uses the description for your existing database and sets the
    connect name alias to ``mynetalias``, which is the identifier used when
    adding the wallet entry.

4.  Add the following wallet location entry in the :ref:`sqlnet.ora
    <optnetfiles>` file, using the ``DIRECTORY`` you created the wallet in::

        WALLET_LOCATION =
            (SOURCE =
                (METHOD = FILE)
                (METHOD_DATA =
                    (DIRECTORY = /home/oracle/wallet_dir)
                )
            )
        SQLNET.WALLET_OVERRIDE = TRUE

    Examine the Oracle documentation for full settings and values.

5.  Ensure the configuration files are in a default location or TNS_ADMIN is
    set to the directory containing them.  See :ref:`optnetfiles`.

With an Oracle wallet configured, and readable by you, your scripts
can connect to Oracle Database with:

- Standalone connections by setting the ``externalauth`` parameter to *True*
  in :meth:`oracledb.connect()` as shown below:

  .. code-block:: python

    connection = oracledb.connect(externalauth=True, dsn="mynetalias")

- Or pooled connections by setting the ``externalauth`` parameter to *True*
  in :meth:`oracledb.create_pool()`.  Additionally in python-oracledb Thick
  mode, you must set the ``homogeneous`` parameter to *False* as shown below
  since heterogeneous pools can only be used with external authentication:

  .. code-block:: python

    pool = oracledb.create_pool(externalauth=True, homogeneous=False,
                                dsn="mynetalias")
    pool.acquire()

The ``dsn`` used in :meth:`oracledb.connect()` and
:meth:`oracledb.create_pool()` must match the one used in the wallet.

After connecting, the query::

    SELECT SYS_CONTEXT('USERENV', 'SESSION_USER') FROM DUAL;

will show::

    MYUSER

.. note::

    Wallets are also used to configure Transport Layer Security (TLS) connections.
    If you are using a wallet like this, you may need a database username and password
    in :meth:`oracledb.connect()` and :meth:`oracledb.create_pool()` calls.

**External Authentication and Proxy Authentication**

The following examples show external wallet authentication combined with
:ref:`proxy authentication <proxyauth>`.  These examples use the wallet
configuration from above, with the addition of a grant to another user::

    ALTER USER mysessionuser GRANT CONNECT THROUGH myuser;

After connection, you can check who the session user is with:

.. code-block:: sql

    SELECT SYS_CONTEXT('USERENV', 'PROXY_USER'),
           SYS_CONTEXT('USERENV', 'SESSION_USER')
    FROM DUAL;

Standalone connection example:

.. code-block:: python

    # External Authentication with proxy
    connection = oracledb.connect(user="[mysessionuser]", dsn="mynetalias")
    # PROXY_USER:   MYUSER
    # SESSION_USER: MYSESSIONUSER

You can also explicitly set the ``externalauth`` parameter to True in standalone
connections as shown below. The ``externalauth`` parameter is optional.

.. code-block:: python

    # External Authentication with proxy when externalauth is set to True
    connection = oracledb.connect(user="[mysessionuser]", dsn="mynetalias",
                                  externalauth=True)
    # PROXY_USER:   MYUSER
    # SESSION_USER: MYSESSIONUSER

Pooled connection example:

.. code-block:: python

    # External Authentication with proxy
    pool = oracledb.create_pool(externalauth=True, homogeneous=False,
                                dsn="mynetalias")
    pool.acquire(user="[mysessionuser]")
    # PROXY_USER:   MYUSER
    # SESSION_USER: MYSESSIONUSER

The following usage is not supported:

.. code-block:: python

    pool = oracledb.create_pool(user="[mysessionuser]", externalauth=True,
                                homogeneous=False, dsn="mynetalias")
    pool.acquire()

.. _opsysauth:

Operating System Authentication
-------------------------------

With `Operating System <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-37BECE32-58D5-43BF-A098-97936D66968F>`__ authentication, Oracle allows
user authentication to be performed by the operating system.  The following
steps give an overview of how to implement OS Authentication on Linux.

1.  Log in to your computer. The commands used in these steps assume the
    operating system user name is "oracle".

2.  Log in to SQL*Plus as the SYSTEM user and verify the value for the
    ``OS_AUTHENT_PREFIX`` parameter::

        SQL> SHOW PARAMETER os_authent_prefix

        NAME                                 TYPE        VALUE
        ------------------------------------ ----------- ------------------------------
        os_authent_prefix                    string      ops$

3.  Create an Oracle database user using the ``os_authent_prefix`` determined in
    step 2, and the operating system user name:

   .. code-block:: sql

        CREATE USER ops$oracle IDENTIFIED EXTERNALLY;
        GRANT CONNECT, RESOURCE TO ops$oracle;

In Python, connect using the following code:

.. code-block:: python

       connection = oracledb.connect(dsn="mynetalias")

Your session user will be ``OPS$ORACLE``.

If your database is not on the same computer as Python, you can perform testing
by setting the database configuration parameter ``remote_os_authent=true``.
Beware of security concerns because this is insecure.

See `Oracle Database Security Guide
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-37BECE32-58D5-43BF-A098-97936D66968F>`__ for more information about
Operating System Authentication.

.. _tokenauth:

Token-Based Authentication
==========================

Token-Based Authentication allows users to connect to a database by using an
encrypted authentication token without having to enter a database username and
password.  The authentication token must be valid and not expired for the
connection to be successful.  Users already connected will be able to continue
work after their token has expired but they will not be able to reconnect
without getting a new token.

The two authentication methods supported by python-oracledb are
:ref:`Open Authorization (OAuth 2.0) <oauth2>` and :ref:`Oracle
Cloud Infrastructure (OCI) Identity and Access Management (IAM) <iamauth>`.

.. _oauth2:

Connecting Using OAuth 2.0 Token-Based Authentication
-----------------------------------------------------

Oracle Cloud Infrastructure (OCI) users can be centrally managed in a Microsoft
Azure Active Directory (Azure AD) service. Open Authorization (OAuth 2.0) token-based
authentication allows users to authenticate to Oracle Database using Azure AD OAuth2
tokens. Currently, only Azure AD tokens are supported. Ensure that you have a
Microsoft Azure account and your Oracle Database is registered with Azure AD. See
`Configuring the Oracle Autonomous Database for Microsoft Azure AD Integration
<https://www.oracle.com/pls/topic/lookup?ctx=db19&id=
GUID-0A60F22D-56A3-408D-8EC8-852C38C159C0>`_ for more information.
Both Thin and Thick modes of the python-oracledb driver support OAuth 2.0 token-based
authentication.

When using python-oracledb in Thick mode, Oracle Client libraries 19.15 (or later),
or 21.7 (or later) are needed.

OAuth 2.0 token-based authentication can be used for both standalone connections
and connection pools. Tokens can be specified using the connection parameter
introduced in python-oracledb 1.1. Users of earlier python-oracledb versions
can alternatively use
:ref:`OAuth 2.0 Token-Based Authentication Connection Strings<oauth2connstr>`.

OAuth2 Token Generation And Extraction
++++++++++++++++++++++++++++++++++++++

There are different ways to retrieve Azure AD OAuth2 tokens. Some of the ways to
retrieve the OAuth2 tokens are detailed in `Examples of Retrieving Azure AD OAuth2
Tokens <https://www.oracle.com/pls/topic/lookup?ctx=db19&id=
GUID-3128BDA4-A233-48D8-A2B1-C8380DBDBDCF>`_. You can also retrieve Azure AD OAuth2
tokens by using `Azure Identity client library for Python
<https://docs.microsoft.com/en-us/python/api/overview/azure/identity-readme?view=
azure-python>`_.

.. _oauthhandler:

Example of Using a TokenHandlerOAuth Class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here, as an example, we are using a Python script to automate the
process of generating and reading the Azure AD OAuth2 tokens.

.. code:: python

    import json
    import os

    import oracledb
    import requests

    class TokenHandlerOAuth:

        def __init__(self,
                     file_name="cached_token_file_name",
                     api_key="api_key",
                     client_id="client_id",
                     client_secret="client_secret"):
            self.token = None
            self.file_name = file_name
            self.url = \
                f"https://login.microsoftonline.com/{api_key}/oauth2/v2.0/token"
            self.scope = \
                f"https://oracledevelopment.onmicrosoft.com/{client_id}/.default"
            if os.path.exists(file_name):
                with open(file_name) as f:
                    self.token = f.read().strip()
            self.api_key = api_key
            self.client_id = client_id
            self.client_secret = client_secret

        def __call__(self, refresh):
            if self.token is None or refresh:
                post_data = dict(client_id=self.client_id,
                                 grant_type="client_credentials",
                                 scope=self.scope,
                                 client_secret=self.client_secret)
                r = requests.post(url=self.url, data=post_data)
                result = json.loads(r.text)
                self.token = result["access_token"]
                with open(self.file_name, "w") as f:
                    f.write(self.token)
            return self.token

The TokenHandlerOAuth class uses a callable to generate and read the OAuth2
tokens. When the callable in the TokenHandlerAuth class is invoked for the
first time to create a standalone connection or pool, the ``refresh`` parameter
is False which allows the callable to return a cached token, if desired. The
expiry date is then extracted from this token and compared with the current
date. If the token has not expired, then it will be used directly. If the token
has expired, the callable is invoked the second time with the ``refresh``
parameter set to True.

See :ref:`curl` for an alternative way to generate the tokens.

Standalone Connection Creation with OAuth2 Access Tokens
++++++++++++++++++++++++++++++++++++++++++++++++++++++++

For OAuth 2.0 Token-Based Authentication, the ``access_token`` connection parameter
must be specified. This parameter should be a string (or a callable that returns a
string) specifying an Azure AD OAuth2 token.

Standalone connections can be created in the python-oracledb Thick and Thin modes
using OAuth 2.0 token-based authentication. In the examples below, the
``access_token`` parameter is set to a callable.

**In python-oracledb Thin mode**

When connecting to Oracle Cloud Database with mutual TLS (mTLS) using OAuth2
tokens in the python-oracledb Thin mode, you need to explicitly set the
``config_dir``, ``wallet_location``, and ``wallet_password`` parameters of
:func:`~oracledb.connect`. See, :ref:`autonomousdb`.
The following example shows a standalone connection creation using OAuth 2.0 token
based authentication in the python-oracledb Thin mode. For information on
TokenHandlerOAuth() used in the example, see :ref:`oauthhandler`.

.. code:: python

    connection = oracledb.connect(access_token=TokenHandlerOAuth(),
                                  dsn=mydb_low,
                                  config_dir="path_to_extracted_wallet_zip",
                                  wallet_location="location_of_pem_file",
                                  wallet_password=wp)

**In python-oracledb Thick mode**

In the python-oracledb Thick mode, you can create a standalone connection using
OAuth2 tokens as shown in the example below. For information on
TokenHandlerOAuth() used in the example, see :ref:`oauthhandler`.

.. code:: python

    connection = oracledb.connect(access_token=TokenHandlerOAuth(),
                                  externalauth=True,
                                  dsn=mydb_low)

Connection Pool Creation with OAuth2 Access Tokens
++++++++++++++++++++++++++++++++++++++++++++++++++

For OAuth 2.0 Token-Based Authentication, the ``access_token`` connection
parameter must be specified. This parameter should be a string (or a callable
that returns a string) specifying an Azure AD OAuth2 token.

The ``externalauth`` parameter must be set to True in the python-oracledb Thick
mode.  The ``homogeneous`` parameter must be set to True in both the
python-oracledb Thin and Thick modes.

Connection pools can be created in the python-oracledb Thick and Thin modes
using OAuth 2.0 token-based authentication. In the examples below, the
``access_token`` parameter is set to a callable.

Note that the ``access_token`` parameter should be set to a callable. This is
useful when the connection pool needs to expand and create new connections but
the current token has expired. In such case, the callable should return a
string specifying the new, valid Azure AD OAuth2 token.

**In python-oracledb Thin mode**

When connecting to Oracle Cloud Database with mutual TLS (mTLS) using OAuth2
tokens in the python-oracledb Thin mode, you need to explicitly set the
``config_dir``, ``wallet_location``, and ``wallet_password`` parameters of
:func:`~oracledb.create_pool`. See, :ref:`autonomousdb`.
The following example shows a connection pool creation using OAuth 2.0 token
based authentication in the python-oracledb Thin mode. For information on
TokenHandlerOAuth() used in the example, see :ref:`oauthhandler`.

.. code:: python

    connection = oracledb.create_pool(access_token=TokenHandlerOAuth(),
                                      homogeneous=True, dsn=mydb_low,
                                      config_dir="path_to_extracted_wallet_zip",
                                      wallet_location="location_of_pem_file",
                                      wallet_password=wp
                                      min=1, max=5, increment=2)

**In python-oracledb Thick mode**

In the python-oracledb Thick mode, you can create a connection pool using
OAuth2 tokens as shown in the example below. For information on
TokenHandlerOAuth() used in the example, see :ref:`oauthhandler`.

.. code:: python

    pool = oracledb.create_pool(access_token=TokenHandlerOAuth(),
                                externalauth=True, homogeneous=True,
                                dsn=mydb_low, min=1, max=5, increment=2)

.. _oauth2connstr:

OAuth 2.0 Token-Based Authentication Connection Strings
+++++++++++++++++++++++++++++++++++++++++++++++++++++++

The connection string used by python-oracledb can specify the directory where
the token file is located. This syntax is usable with older versions of
python-oracledb. However, it is recommended to use connection parameters
introduced in python-oracledb 1.1 instead. See
:ref:`OAuth 2.0 Token-Based Authentication<oauth2>`.

.. note::

    OAuth 2.0 Token-Based Authentication Connection Strings is only supported in
    the python-oracledb Thick mode. See :ref:`enablingthick`.

There are different ways to retrieve Azure AD OAuth2 tokens. Some of the ways to
retrieve the OAuth2 tokens are detailed in `Examples of Retrieving Azure AD OAuth2
Tokens <https://www.oracle.com/pls/topic/lookup?ctx=db19&id=
GUID-3128BDA4-A233-48D8-A2B1-C8380DBDBDCF>`_. You can also retrieve Azure AD OAuth2
tokens by using `Azure Identity client library for Python
<https://docs.microsoft.com/en-us/python/api/overview/azure/identity-readme?view=
azure-python>`_.

.. _curl:

Example of Using a Curl Command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here, as an example, we are using Curl with a Resource Owner
Password Credential (ROPC) Flow, that is, a ``curl`` command is used against
the Azure AD API to get the Azure AD OAuth2 token::

    curl -X POST -H 'Content-Type: application/x-www-form-urlencoded'
    https://login.microsoftonline.com/your_tenant_id/oauth2/v2.0/token
    -d 'client_id=your_client_id'
    -d 'grant_type=client_credentials'
    -d 'scope=https://oracledevelopment.onmicrosoft.com/your_client_id/.default'
    -d 'client_secret=your_client_secret'

This command generates a JSON response with token type, expiration, and access
token values. The JSON response needs to be parsed so that only the access
token is written and stored in a file. You can save the value of
``access_token`` generated to a file and set ``TOKEN_LOCATION`` to the location
of token file. See :ref:`oauthhandler` for an example of using the
TokenHandlerOAuth class to generate and read tokens.

The Oracle Net parameters ``TOKEN_AUTH`` and ``TOKEN_LOCATION`` must be set when
you are using the connection string syntax. Also, the ``PROTOCOL``
parameter must be ``tcps`` and ``SSL_SERVER_DN_MATCH`` should be ``ON``.

You can set ``TOKEN_AUTH=OAUTH``. There is no default location set in this
case, so you must set ``TOKEN_LOCATION`` to either of the following:

*  A directory, in which case, you must create a file named ``token`` which
   contains the token value
*  A fully qualified file name, in which case, you must specify the entire path
   of the file which contains the token value

You can either set ``TOKEN_AUTH`` and ``TOKEN_LOCATION`` in a :ref:`sqlnet.ora
<optnetfiles>` file or alternatively, you can specify it inside a :ref:`Connect
Descriptor <conndescriptor>`, for example when using a :ref:`tnsnames.ora
<optnetfiles>` file::

    db_alias =
        (DESCRIPTION =
            (ADDRESS=(PROTOCOL=TCPS)(PORT=1522)(HOST=xxx.oraclecloud.com))
            (CONNECT_DATA=(SERVICE_NAME=xxx.adb.oraclecloud.com))
            (SECURITY =
                (SSL_SERVER_CERT_DN="CN=xxx.oraclecloud.com, \
                 O=Oracle Corporation,L=Redwood City,ST=California,C=US")
                (TOKEN_AUTH=OAUTH)
                (TOKEN_LOCATION="/home/user1/mytokens/oauthtoken")
            )
        )

The ``TOKEN_AUTH`` and ``TOKEN_LOCATION`` values in a connection string take
precedence over the ``sqlnet.ora`` settings.

Standalone connection example:

.. code-block:: python

    connection = oracledb.connect(dsn=db_alias, externalauth=True)

Connection pool example:

.. code-block:: python

    pool = oracledb.create_pool(dsn=db_alias, externalauth=True,
                                homogeneous=False, min=1, max=2, increment=1)

    connection = pool.acquire()


.. _iamauth:

Connecting Using OCI IAM Token-Based Authentication
---------------------------------------------------

Oracle Cloud Infrastructure (OCI) Identity and Access Management (IAM) provides
its users with a centralized database authentication and authorization system.
Using this authentication method, users can use the database access token issued
by OCI IAM to authenticate to the Oracle Cloud Database. Both Thin and Thick modes
of the python-oracledb driver support OCI IAM token-based authentication.

When using python-oracledb in Thick mode, Oracle Client libraries 19.14 (or later),
or 21.5 (or later) are needed.

OCI IAM token-based authentication can be used for both standalone connections and
connection pools. Tokens can be specified using the connection parameter
introduced in python-oracledb 1.1. Users of earlier python-oracledb versions
can alternatively use :ref:`OCI IAM Token-Based Authentication Connection Strings
<iamauthconnstr>`.

OCI IAM Token Generation and Extraction
+++++++++++++++++++++++++++++++++++++++

Authentication tokens can be generated through execution of an Oracle Cloud
Infrastructure command line interface (OCI-CLI) command ::

    oci iam db-token get

On Linux, a folder ``.oci/db-token`` will be created in your home directory.
It will contain the token and private key files needed by python-oracledb.

.. _iamhandler:

Example of Using a TokenHandlerIAM Class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here, as an example, we are using a Python script to automate the process of
generating and reading the OCI IAM tokens.

.. code:: python

    import os

    import oracledb

    class TokenHandlerIAM:

        def __init__(self,
                     dir_name="dir_name",
                     command="oci iam db-token get"):
            self.dir_name = dir_name
            self.command = command
            self.token = None
            self.private_key = None

        def __call__(self, refresh):
            if refresh:
                if os.system(self.command) != 0:
                    raise Exception("token command failed!")
            if self.token is None or refresh:
                self.read_token_info()
            return (self.token, self.private_key)

        def read_token_info(self):
            token_file_name = os.path.join(self.dir_name, "token")
            pkey_file_name = os.path.join(self.dir_name, "oci_db_key.pem")
            with open(token_file_name) as f:
                self.token = f.read().strip()
            with open(pkey_file_name) as f:
                if oracledb.is_thin_mode():
                    self.private_key = f.read().strip()
                else:
                    lines = [s for s in f.read().strip().split("\n")
                             if s not in ('-----BEGIN PRIVATE KEY-----',
                                          '-----END PRIVATE KEY-----')]
                    self.private_key = "".join(lines)

The TokenHandlerIAM class uses a callable to generate and read the OCI IAM
tokens. When the callable in the TokenHandlerIAM class is invoked for the first
time to create a standalone connection or pool, the ``refresh`` parameter is
False which allows the callable to return a cached token, if desired. The
expiry date is then extracted from this token and compared with the current
date. If the token has not expired, then it will be used directly. If the token
has expired, the callable is invoked the second time with the ``refresh``
parameter set to True.

Standalone Connection Creation with OCI IAM Access Tokens
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

For OCI IAM Token-Based Authentication, the ``access_token`` connection parameter
must be specified. This parameter should be a 2-tuple (or a callable that returns
a 2-tuple) containing the token and private key.

Standalone connections can be created in the python-oracledb Thick and Thin modes
using OCI IAM token-based authentication. In the examples below, the
``access_token`` parameter is set to a callable.

**In python-oracledb Thin mode**

When connecting to Oracle Cloud Database with mutual TLS (mTLS) using OCI IAM
tokens in the python-oracledb Thin mode, you need to explicitly set the
``config_dir``, ``wallet_location``, and ``wallet_password`` parameters of
:func:`~oracledb.connect`. See, :ref:`autonomousdb`.
The following example shows a standalone connection creation using OCI IAM token
based authentication in the python-oracledb Thin mode. For information on
TokenHandlerIAM() used in the example, see :ref:`iamhandler`.

.. code:: python

    connection = oracledb.connect(access_token=TokenHandlerIAM(),
                                  dsn=mydb_low,
                                  config_dir="path_to_extracted_wallet_zip",
                                  wallet_location="location_of_pem_file",
                                  wallet_password=wp)

**In python-oracledb Thick mode**

In the python-oracledb Thick mode, you can create a standalone connection using
OCI IAM tokens as shown in the example below. For information on
TokenHandlerIAM() used in the example, see :ref:`iamhandler`.

.. code:: python

    connection = oracledb.connect(access_token=TokenHandlerIAM(),
                                  externalauth=True,
                                  dsn=mydb_low)

Connection Pool Creation with OCI IAM Access Tokens
+++++++++++++++++++++++++++++++++++++++++++++++++++

For OCI IAM Token-Based Authentication, the ``access_token`` connection
parameter must be specified. This parameter should be a 2-tuple (or a callable
that returns a 2-tuple) containing the token and private key.

The ``externalauth`` parameter must be set to True in the python-oracledb Thick
mode.  The ``homogeneous`` parameter must be set to True in both the
python-oracledb Thin and Thick modes.

Connection pools can be created in the python-oracledb Thick and Thin modes
using OCI IAM token-based authentication. In the examples below, the
``access_token`` parameter is set to a callable.

Note that the ``access_token`` parameter should be set to a callable. This is
useful when the connection pool needs to expand and create new connections but
the current token has expired. In such case, the callable should return a
2-tuple (token, private key) specifying the new, valid access token.

**In python-oracledb Thin mode**

When connecting to Oracle Cloud Database with mutual TLS (mTLS) using OCI IAM
tokens in the python-oracledb Thin mode, you need to explicitly set the
``config_dir``, ``wallet_location``, and ``wallet_password`` parameters of
:func:`~oracledb.create_pool`. See, :ref:`autonomousdb`.
The following example shows a connection pool creation using OCI IAM token
based authentication in the python-oracledb Thin mode. For information on
TokenHandlerIAM() used in the example, see :ref:`iamhandler`.

.. code:: python

    connection = oracledb.connect(access_token=TokenHandlerIAM(),
                                  homogeneous=True, dsn=mydb_low,
                                  config_dir="path_to_extracted_wallet_zip",
                                  wallet_location="location_of_pem_file",
                                  wallet_password=wp
                                  min=1, max=5, increment=2)

**In python-oracledb Thick mode**

In the python-oracledb Thick mode, you can create a connection pool using
OCI IAM tokens as shown in the example below. For information on
TokenHandlerIAM() used in the example, see :ref:`iamhandler`.

.. code:: python

    pool = oracledb.create_pool(access_token=TokenHandlerIAM(),
                                externalauth=True,
                                homogeneous=True,
                                dsn=mydb_low,
                                min=1, max=5, increment=2)

.. _iamauthconnstr:

OCI IAM Token-Based Authentication Connection Strings
+++++++++++++++++++++++++++++++++++++++++++++++++++++

The connection string used by python-oracledb can specify the directory where
the token and private key files are located. This syntax is usable with older
versions of python-oracledb. However, it is recommended to use connection
parameters introduced in python-oracledb 1.1 instead. See
:ref:`OCI IAM Token-Based Authentication<iamauth>`.

.. note::

    OCI IAM Token-Based Authentication Connection Strings is only supported in
    the python-oracledb Thick mode. See :ref:`enablingthick`.

The Oracle Cloud Infrastructure command line interface (OCI-CLI) can be used
externally to get tokens and private keys from OCI IAM, for example with the
OCI-CLI ``oci iam db-token get`` command.

The Oracle Net parameter ``TOKEN_AUTH`` must be set when you are using the
connection string syntax. Also, the ``PROTOCOL`` parameter must be ``tcps``
and ``SSL_SERVER_DN_MATCH`` should be ``ON``.

You can set ``TOKEN_AUTH=OCI_TOKEN`` in a ``sqlnet.ora`` file.  Alternatively,
you can specify it in a :ref:`Connect Descriptor <conndescriptor>`, for example
when using a :ref:`tnsnames.ora <optnetfiles>` file::

    db_alias =
        (DESCRIPTION =
            (ADDRESS=(PROTOCOL=TCPS)(PORT=1522)(HOST=xxx.oraclecloud.com))
            (CONNECT_DATA=(SERVICE_NAME=xxx.adb.oraclecloud.com))
            (SECURITY =
                (SSL_SERVER_CERT_DN="CN=xxx.oraclecloud.com, \
                 O=Oracle Corporation,L=Redwood City,ST=California,C=US")
                (TOKEN_AUTH=OCI_TOKEN)
            )
        )

The default location for the token and private key is the same default location
that the OCI-CLI tool writes to. For example ``~/.oci/db-token/`` on Linux.

If the token and private key files are not in the default location then their
directory must be specified with the ``TOKEN_LOCATION`` parameter in a
:ref:`sqlnet.ora <optnetfiles>` file or in a :ref:`Connect Descriptor
<conndescriptor>`, for example when using a :ref:`tnsnames.ora <optnetfiles>`
file::

    db_alias =
        (DESCRIPTION =
            (ADDRESS=(PROTOCOL=TCPS)(PORT=1522)(HOST=xxx.oraclecloud.com))
            (CONNECT_DATA=(SERVICE_NAME=xxx.adb.oraclecloud.com))
            (SECURITY =
                (SSL_SERVER_CERT_DN="CN=xxx.oraclecloud.com, \
                 O=Oracle Corporation,L=Redwood City,ST=California,C=US")
                (TOKEN_AUTH=OCI_TOKEN)
                (TOKEN_LOCATION="/path/to/token/folder")
            )
        )

The ``TOKEN_AUTH`` and ``TOKEN_LOCATION`` values in a connection string take
precedence over the ``sqlnet.ora`` settings.

Standalone connection example:

.. code-block:: python

    connection = oracledb.connect(dsn=db_alias, externalauth=True)

Connection pool example:

.. code-block:: python

    pool = oracledb.create_pool(dsn=db_alias, externalauth=True,
                                homogeneous=False, min=1, max=2, increment=1)

    connection = pool.acquire()


Privileged Connections
======================

The ``mode`` parameter of the function :meth:`oracledb.connect()` specifies
the database privilege that you want to associate with the user.

The example below shows how to connect to Oracle Database as SYSDBA:

.. code-block:: python

    connection = oracledb.connect(user="sys", password=syspwd,
                                  dsn="dbhost.example.com/orclpdb",
                                  mode=oracledb.AUTH_MODE_SYSDBA)

    with connection.cursor() as cursor:
        cursor.execute("GRANT SYSOPER TO hr")

This is equivalent to executing the following in SQL*Plus:

.. code-block:: sql

    CONNECT sys/syspwd@dbhost.example.com/orclpdb AS SYSDBA
    GRANT SYSOPER TO hr;


In python-oracledb Thick mode, when python-oracledb uses Oracle Client
libraries from a database software installation, you can use "bequeath"
connections to databases that are also using the same libraries.  Do this by
setting the standard Oracle environment variables such as ``ORACLE_HOME`` and
``ORACLE_SID`` and connecting in Python like:

.. code-block:: python

    oracledb.init_oracle_client()

    conn = oracledb.connect(mode=oracledb.SYSDBA)

This is equivalent to executing the following in SQL*Plus:

.. code-block:: sql

    CONNECT / AS SYSDBA

.. _netencrypt:

Securely Encrypting Network Traffic to Oracle Database
======================================================

You can encrypt data transferred between the Oracle Database and
python-oracledb so that unauthorized parties are not able to view plain text
values as the data passes over the network.

Both python-oracledb Thin and Thick modes support TLS.  Refer to the `Oracle
Database Security Guide <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-41040F53-D7A6-48FA-A92A-0C23118BC8A0>`__ for more configuration
information.

.. _nne:

Native Network Encryption
-------------------------

The python-oracledb :ref:`Thick mode <enablingthick>` can additionally use
Oracle Database's `native network encryption
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-7F12066A-2BA1-476C-809B-BB95A3F727CF>`__.

With native network encryption, the client and database server negotiate a key
using Diffie-Hellman key exchange.  This provides protection against
man-in-the-middle attacks.

Native network encryption can be configured by editing Oracle Net's optional
:ref:`sqlnet.ora <optnetfiles>` configuration file.  The file on either the
database server and/or on each python-oracledb 'client' machine can be
configured.  Parameters control whether data integrity checking and encryption
is required or just allowed, and which algorithms the client and server should
consider for use.

As an example, to ensure all connections to the database are checked for
integrity and are also encrypted, create or edit the Oracle Database
``$ORACLE_HOME/network/admin/sqlnet.ora`` file.  Set the checksum negotiation
to always validate a checksum and set the checksum type to your desired value.
The network encryption settings can similarly be set.  For example, to use the
SHA512 checksum and AES256 encryption use::

    SQLNET.CRYPTO_CHECKSUM_SERVER = required
    SQLNET.CRYPTO_CHECKSUM_TYPES_SERVER = (SHA512)
    SQLNET.ENCRYPTION_SERVER = required
    SQLNET.ENCRYPTION_TYPES_SERVER = (AES256)

If you definitely know that the database server enforces integrity and
encryption, then you do not need to configure python-oracledb separately.  However,
you can also, or alternatively do so, depending on your business needs.  Create
a ``sqlnet.ora`` on your client machine and locate it with other
:ref:`optnetfiles`::

    SQLNET.CRYPTO_CHECKSUM_CLIENT = required
    SQLNET.CRYPTO_CHECKSUM_TYPES_CLIENT = (SHA512)
    SQLNET.ENCRYPTION_CLIENT = required
    SQLNET.ENCRYPTION_TYPES_CLIENT = (AES256)

The client and server sides can negotiate the protocols used if the settings
indicate more than one value is accepted.

Note that these are example settings only. You must review your security
requirements and read the documentation for your Oracle version. In particular,
review the available algorithms for security and performance.

The NETWORK_SERVICE_BANNER column of the database view
`V$SESSION_CONNECT_INFO <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-9F0DCAEA-A67E-4183-89E7-B1555DC591CE>`__ can be used to verify the
encryption status of a connection. For example with SQL*Plus::

    SQL> select network_service_banner from v$session_connect_info;

If the connection is encrypted, then this query prints an output that includes
the available encryption service, the crypto-checksumming service, and the
algorithms in use, such as::

    NETWORK_SERVICE_BANNER
    -------------------------------------------------------------------------------------
    TCP/IP NT Protocol Adapter for Linux: Version 19.0.0.0.0 - Production
    Encryption service for Linux: Version 19.0.1.0.0 - Production
    AES256 Encryption service adapter for Linux: Version 19.0.1.0.0 - Production
    Crypto-checksumming service for Linux: Version 19.0.1.0.0 - Production
    SHA256 Crypto-checksumming service adapter for Linux: Version 19.0.1.0.0 - Production

If the connection is unencrypted, then the query will only print the
available encryption and crypto-checksumming services in the output. For example::

    NETWORK_SERVICE_BANNER
    -------------------------------------------------------------------------------------
    TCP/IP NT Protocol Adapter for Linux: Version 19.0.0.0.0 - Production
    Encryption service for Linux: Version 19.0.1.0.0 - Production
    Crypto-checksumming service for Linux: Version 19.0.1.0.0 - Production

For more information about Oracle Data Network Encryption and Integrity,
and for information about configuring TLS network encryption, refer to
the `Oracle Database Security Guide <https://www.oracle.com/pls/topic/
lookup?ctx=dblatest&id=DBSEG>`__.

Resetting Passwords
===================

After connecting to Oracle Database, passwords can be changed by calling
:meth:`Connection.changepassword()`:

.. code-block:: python

    # Get the passwords from somewhere, such as prompting the user
    oldpwd = getpass.getpass(f"Old Password for {username}: ")
    newpwd = getpass.getpass(f"New Password for {username}: ")

    connection.changepassword(oldpwd, newpwd)

When a password has expired and you cannot connect directly, you can connect
and change the password in one operation by using the ``newpassword`` parameter
of the function :meth:`oracledb.connect()` constructor:

.. code-block:: python

    # Get the passwords from somewhere, such as prompting the user
    oldpwd = getpass.getpass(f"Old Password for {username}: ")
    newpwd = getpass.getpass(f"New Password for {username}: ")

    connection = oracledb.connect(user=username, password=oldpwd,
                                  dsn="dbhost.example.com/orclpdb",
                                  newpassword=newpwd)

.. _autonomousdb:

Connecting to Oracle Cloud Autonomous Databases
================================================

Python applications can connect to Oracle Autonomous Database (ADB) in Oracle
Cloud using one-way TLS (Transport Layer Security) or mutual TLS
(mTLS). One-way TLS and mTLS provide enhanced security for authentication and
encryption.

A database username and password are still required for your application
connections.  If you need to create a new database schema so you do not login
as the privileged ADMIN user, refer to the relevant Oracle Cloud documentation,
for example see `Create Database Users
<https://docs.oracle.com/en/cloud/paas/autonomous-database/adbdu/managing-database-
users.html#GUID-5B94EA60-554A-4BA4-96A3-1D5A3ED5878D>`__ in the Oracle
Autonomous Database manual.

.. _onewaytls:

One-way TLS Connection to Oracle Autonomous Database
----------------------------------------------------

With one-way TLS, python-oracledb applications can connect to Oracle ADB
without using a wallet.  Both Thin and Thick modes of the python-oracledb
driver support one-way TLS.  Applications that use the python-oracledb Thick
mode, can connect to the Oracle ADB through one-way TLS only when using Oracle
Client library versions 19.14 (or later) or 21.5 (or later).

To enable one-way TLS for an ADB instance, complete the following steps in an
Oracle Cloud console in the **Autonomous Database Information** section of the
ADB instance details:

1. Click the **Edit** link next to *Access Control List* to update the Access
   Control List (ACL). The **Edit Access Control List** dialog box is displayed.

2. In the **Edit Access Control List** dialog box, select the type of address
   list entries and the corresponding values. You can include the required IP
   addresses, hostnames, or Virtual Cloud Networks (VCNs).  The ACL limits
   access to only the IP addresses or VCNs that have been defined and blocks
   all other incoming traffic.

3. Navigate back to the ADB instance details page and click the **Edit** link
   next to *Mutual TLS (mTLS) Authentication*. The **Edit Mutual TLS Authentication**
   is displayed.

4. In the **Edit Mutual TLS Authentication** dialog box, deselect the
   **Require mutual TLS (mTLS) authentication** check box to disable the mTLS
   requirement on Oracle ADB and click **Save Changes**.

5. Navigate back to the ADB instance details page and click **DB Connection** on
   the top of the page. A **Database Connection** dialog box is displayed.

6. In the Database Connection dialog box, select TLS from the **Connection Strings**
   drop-down list.

7. Copy the appropriate Connection String of the database instance used by your application.

Applications can connect to your Oracle ADB instance using the database
credentials and the copied :ref:`Connect Descriptor <conndescriptor>`.  For
example, to connect as the ADMIN user:

.. code-block:: python

    cs = '''(description = (retry_count=20)(retry_delay=3)(address=(protocol=tcps)
               (port=1522)(host=xxx.oraclecloud.com))(connect_data=(service_name=xxx.adb.oraclecloud.com))
               (security=(ssl_server_dn_match=yes)(ssl_server_cert_dn="CN=xxx.oraclecloud.com,
               O=Oracle Corporation, L=Redwood City, T=California, C=US")))'''

    connection = oracledb.connect(user="admin", password=pw, dsn=cs)


You can download the ADB connection wallet using the **DB Connection** button
and extract the ``tnsnames.ora`` file, or create one yourself if you prefer to
keep connections strings out of application code, see :ref:`netservice`.

You may be interested in the blog post `Easy wallet-less connections to Oracle
Autonomous Databases in Python
<https://blogs.oracle.com/opal/post/easy-way-to-connect-python-applications-to-oracle-autonomous-databases>`__.

.. _twowaytls:

Mutual TLS (mTLS) Connection to Oracle Autonomous Database
----------------------------------------------------------

To enable python-oracledb connections to Oracle Autonomous Database in Oracle
Cloud using mTLS, a wallet needs to be downloaded from the cloud console.  mTLS
is sometimes called Two-way TLS.

Install the Wallet and Network Configuration Files
++++++++++++++++++++++++++++++++++++++++++++++++++

From the Oracle Cloud console for the database, download the wallet zip file
using the **DB Connection** button.  The zip contains the wallet and network
configuration files.  When downloading the zip, the cloud console will ask you
to create a wallet password.  This password is used by python-oracledb in Thin
mode, but not in Thick mode.

Note: keep wallet files in a secure location and only share them and the
password with authorized users.

**In python-oracledb Thin mode**

For python-oracledb in Thin mode, only two files from the zip are needed:

- ``tnsnames.ora`` - Maps net service names used for application connection
  strings to your database services
- ``ewallet.pem`` - Enables SSL/TLS connections in Thin mode. Keep this file
  secure

If you do not have a PEM file, see :ref:`createpem`.

Unzip the wallet zip file and move the required files to a location such as
``/opt/OracleCloud/MYDB``.

Connection can be made using your database credentials and setting the ``dsn``
parameter to the desired network alias from the ``tnsnames.ora`` file.  The
``config_dir`` parameter indicates the directory containing ``tnsnames.ora``.
The ``wallet_location`` parameter is the directory containing the PEM file.  In
this example the files are in the same directory.  The ``wallet_password``
parameter should be set to the password created in the cloud console when
downloading the wallet. For example, to connect as the ADMIN user using the
``mydb_low`` network service name:

.. code-block:: python

    connection = oracledb.connect(user="admin", password=pw, dsn="mydb_low",
                                  config_dir="/opt/OracleCloud/MYDB",
                                  wallet_location="/opt/OracleCloud/MYDB",
                                  wallet_password=wp)

**In python-oracledb Thick mode**

For python-oracledb in Thick mode, only these files from the zip are needed:

- ``tnsnames.ora`` - Maps net service names used for application connection
  strings to your database services
- ``sqlnet.ora`` - Configures Oracle Network settings
- ``cwallet.sso`` - Enables SSL/TLS connections in Thick mode.  Keep this file
  secure

Unzip the wallet zip file.  There are two options for placing the required
files:

- Move the three files to the ``network/admin`` directory of the client
  libraries used by your application. For example if you are using Instant
  Client 19c and it is in ``$HOME/instantclient_19_15``, then you would put the
  wallet files in ``$HOME/instantclient_19_15/network/admin/``.

  Connection can be made using your database credentials and setting the
  ``dsn`` parameter to the desired network alias from the ``tnsnames.ora``
  file.  For example, to connect as the ADMIN user using the ``mydb_low``
  network service name:

  .. code-block:: python

       connection = oracledb.connect(user="admin", password=pw, dsn="mydb_low")

- Alternatively, move the three files to any accessible directory, for example
  ``/opt/OracleCloud/MYDB``.

  Then edit ``sqlnet.ora`` and change the wallet location directory to the
  directory containing the ``cwallet.sso`` file.  For example::

    WALLET_LOCATION = (SOURCE = (METHOD = file) (METHOD_DATA = (DIRECTORY="/opt/OracleCloud/MYDB")))
    SSL_SERVER_DN_MATCH=yes

  Since the ``tnsnames.ora`` and ``sqlnet.ora`` files are not in the default
  location, your application needs to indicate where they are, either with the
  ``config_dir`` parameter to :meth:`oracledb.init_oracle_client()`, or using
  the ``TNS_ADMIN`` environment variable.  See :ref:`Optional Oracle Net
  Configuration Files <optnetfiles>`.  (Neither of these settings are needed,
  and you do not need to edit ``sqlnet.ora``, if you have put all the files in
  the ``network/admin`` directory.)

  For example, to connect as the ADMIN user using the ``mydb_low`` network
  service name:

  .. code-block:: python

       oracledb.init_oracle_client(config_dir="/opt/OracleCloud/MYDB")

       connection = oracledb.connect(user="admin", password=pw, dsn="mydb_low")


In python-oracle Thick mode, to create mTLS connections in one Python process
to two or more Oracle Autonomous Databases, move each ``cwallet.sso`` file to
its own directory.  For each connection use different connection string
``WALLET_LOCATION`` parameters to specify the directory of each ``cwallet.sso``
file.  It is recommended to use Oracle Client libraries 19.17 (or later) when
using :ref:`multiple wallets <connmultiwallets>`.

Using the Easy Connect Syntax with Oracle Autonomous Database
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

When python-oracledb is using Oracle Client libraries 19c, or later, you can
optionally use :ref:`Easy Connect <easyconnect>` syntax to connect to Oracle
Autonomous Database.

The mapping from the cloud ``tnsnames.ora`` entries to an Easy Connect string
is::

    protocol://host:port/service_name?wallet_location=/my/dir&retry_count=N&retry_delay=N

For example, if your ``tnsnames.ora`` file had an entry::

    cjjson_high = (description=(retry_count=20)(retry_delay=3)
        (address=(protocol=tcps)(port=1522)
        (host=xxx.oraclecloud.com))
        (connect_data=(service_name=abc_cjjson_high.adb.oraclecloud.com))
        (security=(ssl_server_cert_dn="CN=xxx.oraclecloud.com,O=Oracle Corporation,L=Redwood City,ST=California,C=US")))

Then your applications can connect using the connection string:

.. code-block:: python

    dsn = "tcps://xxx.oraclecloud.com:1522/abc_cjjson_high.adb.oraclecloud.com?wallet_location=/Users/cjones/Cloud/CJJSON&retry_count=20&retry_delay=3"
    connection = oracledb.connect(user="hr", password=userpwd, dsn=dsn)

The ``wallet_location`` parameter needs to be set to the directory containing
the ``cwallet.sso`` or ``ewallet.pem`` file from the wallet zip.  The other
wallet files, including ``tnsnames.ora``, are not needed when you use the Easy
Connect syntax.

You can add other Easy Connect parameters to the connection string, for example::

    dsn = dsn + "&https_proxy=myproxy.example.com&https_proxy_port=80"

With python-oracledb Thin mode, the wallet password needs to be passed as a
connection parameter.

.. _createpem:

Creating a PEM File for python-oracledb Thin Mode
+++++++++++++++++++++++++++++++++++++++++++++++++

For mutual TLS in python-oracledb Thin mode, the certificate must be Privacy
Enhanced Mail (PEM) format. If you are using Oracle Autonomous Database your
wallet zip file will already include a PEM file.

If you have a PKCS12 ``ewallet.p12`` file and need to create PEM file, you can
use third party tools or the script below to do a conversion. For example, you
can invoke the script by passing the wallet password and the directory
containing the PKCS12 file::

    python create_pem.py --wallet-password 'xxxxx' /Users/scott/cloud_configs/MYDBDIR

Once the PEM file has been created, you can use it by passing its directory
location as the ``wallet_location`` parameter to :func:`oracledb.connect()` or
:func:`oracledb.create_pool()`.  These methods also accept a
``wallet_password`` parameter.  See :ref:`twowaytls`.

**Script to convert from PKCS12 to PEM**

.. code-block:: python

    # create_pem.py

    import argparse
    import getpass
    import os

    from cryptography.hazmat.primitives.serialization \
            import pkcs12, Encoding, PrivateFormat, BestAvailableEncryption, \
                   NoEncryption

    # parse command line
    parser = argparse.ArgumentParser(description="convert PKCS#12 to PEM")
    parser.add_argument("wallet_location",
                        help="the directory in which the PKCS#12 encoded "
                             "wallet file ewallet.p12 is found")
    parser.add_argument("--wallet-password",
                        help="the password for the wallet which is used to "
                             "decrypt the PKCS#12 encoded wallet file; if not "
                             "specified, it will be requested securely")
    parser.add_argument("--no-encrypt",
                        dest="encrypt", action="store_false", default=True,
                        help="do not encrypt the converted PEM file with the "
                             "wallet password")
    args = parser.parse_args()

    # validate arguments and acquire password if one was not specified
    pkcs12_file_name = os.path.join(args.wallet_location, "ewallet.p12")
    if not os.path.exists(pkcs12_file_name):
        msg = f"wallet location {args.wallet_location} does not contain " \
               "ewallet.p12"
        raise Exception(msg)
    if args.wallet_password is None:
        args.wallet_password = getpass.getpass()

    pem_file_name = os.path.join(args.wallet_location, "ewallet.pem")
    pkcs12_data = open(pkcs12_file_name, "rb").read()
    result = pkcs12.load_key_and_certificates(pkcs12_data,
                                              args.wallet_password.encode())
    private_key, certificate, additional_certificates = result
    if args.encrypt:
        encryptor = BestAvailableEncryption(args.wallet_password.encode())
    else:
        encryptor = NoEncryption()
    with open(pem_file_name, "wb") as f:
        f.write(private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8,
                                          encryptor))
        f.write(certificate.public_bytes(Encoding.PEM))
        for cert in additional_certificates:
            f.write(cert.public_bytes(Encoding.PEM))
    print("PEM file", pem_file_name, "written.")

.. _firewallproxy:

Connecting Through a Firewall via a Proxy
=========================================

If you are behind a firewall, you can tunnel TLS/SSL connections via a proxy by
setting connection attributes, or by making `HTTPS_PROXY <https://www.oracle.
com/pls/topic/lookup?ctx=dblatest&id=GUID-C672E92D-CE32-4759-9931-
92D7960850F7>`__ proxy name and `HTTPS_PROXY_PORT <https://www.oracle.com/pls/
topic/lookup?ctx=dblatest&id=GUID-E69D27B7-2B59-4946-89B3-5DDD491C2D9A>`__
port parameters available in your :ref:`connection string <connstr>`.

.. note::

    Oracle does not recommend connecting through a firewall via a proxy when
    performance is critical.

**In python-oracledb Thin mode**

- Proxy settings ``https_proxy`` and ``https_proxy_port`` can be passed during
  connection or pool creation.  Use appropriate values for your proxy:

  .. code-block:: python

      connection = oracledb.connect(user="admin", password=pw, dsn="mydb_low",
                                    config_dir="/opt/OracleCloud/MYDB",
                                    wallet_location="/opt/OracleCloud/MYDB", wallet_password=wp,
                                    https_proxy="myproxy.example.com", https_proxy_port=80)

- Alternatively, add the parameters to your :ref:`Easy Connect <easyconnect>`
  string::

      localhost/orclpdb&https_proxy=myproxy.example.com&https_proxy_port=80

- Alternatively, update the :ref:`Connect Descriptor <conndescriptor>` (either
  being passed directly during connection or contained in your
  :ref:`tnsnames.ora <optnetfiles>` file). If you are using a :ref:`tnsnames.ora
  <optnetfiles>` file, a modified entry might look like::

      mydb_low = (description=
                   (address=
                     (https_proxy=myproxy.example.com)(https_proxy_port=80)
                     (protocol=tcps)(port=1522)(host= . . . )

**In python-oracledb Thick mode**

- If you are using an :ref:`Easy Connect <easyconnect>` string, add
  ``HTTPS_PROXY`` and ``HTTPS_PROXY_PORT`` parameters with appropriate values for
  your proxy. For example, you might pass parameters like::

      localhost/orclpdb&https_proxy=myproxy.example.com&https_proxy_port=80

- Alternatively, update the :ref:`Connect Descriptor <conndescriptor>` (either
  being passed directly during connection or contained in your
  :ref:`tnsnames.ora <optnetfiles>` file). If you are using a :ref:`tnsnames.ora
  <optnetfiles>` file, a modified entry might look like::

      mydb_low = (description=
                   (address=
                     (https_proxy=myproxy.example.com)(https_proxy_port=80)
                     (protocol=tcps)(port=1522)(host= . . . )

  Additionally create, or edit, a :ref:`sqlnet.ora <optnetfiles>` file and add
  a line::

      SQLNET.USE_HTTPS_PROXY=on

.. _connmultiwallets:

Connecting using Multiple Wallets
=================================

You can make multiple connections with different wallets in one Python
process.

**In python-oracledb Thin mode**

To use multiple wallets in python-oracledb Thin mode, pass the different
connection strings, wallet locations, and wallet password (if required) in each
:meth:`oracledb.connect()` call or when creating a :ref:`connection pool
<connpooling>`:

.. code-block:: python

    connection = oracledb.connect(user=user_name, password=userpw, dsn=dsn,
                                  config_dir="path_to_extracted_wallet_zip",
                                  wallet_location="location_of_pem_file",
                                  wallet_password=walletpw)

The ``config_dir`` parameter is the directory containing the :ref:`tnsnames.ora
<optnetfiles>` file.  The ``wallet_location`` parameter is the directory
containing the ``ewallet.pem`` file.  If you are using Oracle Autonomous
Database, both of these paths are typically the same directory where the
``wallet.zip`` file was extracted.  The ``dsn`` should specify a TCPS
connection.

**In python-oracledb Thick mode**

To use multiple wallets in python-oracledb Thick mode, a TCPS connection string
containing the ``MY_WALLET_DIRECTORY`` option needs to be created:

.. code-block:: python

    dsn = "mydb_high"   # one of the network aliases from tnsnames.ora
    params = oracledb.ConnectParams(config_dir="path_to_extracted_wallet_zip",
                                    wallet_location="path_location_of_sso_file")
    params.parse_connect_string(dsn)
    dsn = params.get_connect_string()
    connection = oracledb.connect(user=user_name, password=password, dsn=dsn)

The ``config_dir`` parameter should be the directory containing the
:ref:`tnsnames.ora <optnetfiles>` and ``sqlnet.ora`` files.  The
``wallet_location`` parameter is the directory containing the ``cwallet.sso``
file.  If you are using Oracle Autonomous Database, both of these paths are
typically the same directory where the ``wallet.zip`` file was extracted.

.. note::

       Use Oracle Client libraries 19.17, or later, or use Oracle Client 21c or
       23ai.  They contain important bug fixes for using multiple wallets in
       the one process.

.. _connsharding:

Connecting to Oracle Globally Distributed Database
==================================================

`Oracle Globally Distributed Database
<https://www.oracle.com/database/distributed-database/>`__ is a feature of
Oracle Database that lets you automatically distribute and replicate data
across a pool of Oracle databases that share no hardware or software.  It was
previously known as Oracle Sharding.  It allows a database table to be split so
each database contains a table with the same columns but a different subset of
rows.  These tables are known as sharded tables.  From the perspective of an
application, a sharded table in Oracle Globally Distributed Database looks like
a single table: the distribution of data across those shards is completely
transparent to the application.

Sharding is configured in
Oracle Database, see the `Oracle Globally Distributed Database
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=SHARD>`__ manual.  It
requires Oracle Database and Oracle Client libraries 12.2, or later.

.. note::

    Oracle Globally Distributed Database is only supported in the
    python-oracledb Thick mode.  See :ref:`enablingthick`.

The :meth:`oracledb.connect()` and :meth:`ConnectionPool.acquire()` functions
accept ``shardingkey`` and ``supershardingkey`` parameters that are a sequence
of values used to route the connection directly to a given shard.  A sharding
key is always required.  A super sharding key is additionally required when
using composite sharding, which is when data has been partitioned by a list or
range (the super sharding key), and then further partitioned by a sharding key.

When creating a connection pool, the :meth:`oracledb.create_pool()` attribute
``max_sessions_per_shard`` can be set.  This is used to balance connections in
the pool equally across shards.  It requires Oracle Client libraries 18.3 or
later.

Shard key values may be of type string (mapping to VARCHAR2 shard keys), number
(NUMBER), bytes (RAW), or date (DATE).  Multiple types may be used in each
array.  Sharding keys of TIMESTAMP type are not supported.

When connected to a shard, queries will only return data from that shard.  For
queries that need to access data from multiple shards, connections can be
established to the coordinator shard catalog database.  In this case, no shard
key or super shard key is used.

As an example of direct connection, if sharding had been configured on a single
VARCHAR2 column like:

.. code-block:: sql

    CREATE SHARDED TABLE customers (
      cust_id NUMBER,
      cust_name VARCHAR2(30),
      class VARCHAR2(10) NOT NULL,
      signup_date DATE,
      cust_code RAW(20),
      CONSTRAINT cust_name_pk PRIMARY KEY(cust_name))
      PARTITION BY CONSISTENT HASH (cust_name)
      PARTITIONS AUTO TABLESPACE SET ts1;

then direct connection to a shard can be made by passing a single sharding key:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb",
                                  shardingkey=["SCOTT"])

Numbers keys can be used in a similar way:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb",
                                  shardingkey=[110])

When sharding by DATE, you can connect like:

.. code-block:: python

    import datetime

    d = datetime.datetime(2014, 7, 3)

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb",
                                  shardingkey=[d])

When sharding by RAW, you can connect like:

.. code-block:: python

    b = b'\x01\x04\x08';

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb",
                                  shardingkey=[b])

Multiple keys can be specified, for example:

.. code-block:: python

    key_list = [70, "SCOTT", "gold", b'\x00\x01\x02']

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb",
                                  shardingkey=key_list)

A super sharding key example is:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb",
                                  supershardingkey=["goldclass"],
                                  shardingkey=["SCOTT"])
