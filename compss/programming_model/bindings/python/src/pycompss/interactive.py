#
#  Copyright 2.02-2017 Barcelona Supercomputing Center (www.bsc.es)
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
'''@author: fconejer

PyCOMPSs Binding - Interactive API
==================================
Provides the current start and stop for the use of pycompss interactively.
'''

import os
import logging
from tempfile import mkdtemp
import time
# from random import randint
# from multiprocessing import Process
from pycompss.api.api import compss_start
from pycompss.api.api import compss_stop
from pycompss.runtime.binding import get_log_path
from pycompss.runtime.binding import get_pending_to_synchronize
from pycompss.runtime.launch import initialize_compss
from pycompss.util.logs import init_logging
import pycompss.runtime.binding as binding

persistent_storage = False
myUuid = 0
app_path = 'InteractiveMode'  # Warning! The name should start with InteractiveMode due to @task checks it explicitly.
running = False               #          If has to be changed, it is necessary to update the task decorator.
process = None
log_path = '/tmp/'
graphing = False
tracing = False
monitoring = False


def start(log_level='off',
          o_c=False,
          debug=False,
          graph=False,
          trace=False,
          monitor=None,
          project_xml=None,
          resources_xml=None,
          summary=False,
          taskExecution='compss',
          storageConf=None,
          taskCount=50,
          appName='Interactive',
          uuid=None,
          baseLogDir=None,
          specificLogDir=None,
          extraeCfg=None,
          comm='NIO',
          conn='',
          masterName='',
          masterPort='',
          scheduler='es.bsc.compss.scheduler.loadBalancingScheduler.LoadBalancingScheduler',
          jvmWorkers='-Xms1024m,-Xmx1024m,-Xmn400m',
          verbose=False,
          cpuAffinity='automatic',
          gpuAffinity='automatic'
          ):
    launchPath = os.path.dirname(os.path.abspath(__file__))
    # compss_home = launchPath without the last 3 folders (Bindings/python/pycompss/runtime)
    compss_home = os.path.sep.join(launchPath.split(os.path.sep)[:-3])
    os.environ['COMPSS_HOME'] = compss_home

    # Get environment variables
    cp = os.getcwd() + '/'
    pythonPath = os.environ['PYTHONPATH']
    classPath = os.environ['CLASSPATH']
    ld_library_path = os.environ['LD_LIBRARY_PATH']

    # Set extrae dependencies
    extrae_home = compss_home + '/Dependencies/extrae'
    extrae_lib = extrae_home + '/lib'
    os.environ['EXTRAE_HOME'] = extrae_home
    os.environ['LD_LIBRARY_PATH'] = extrae_lib + ':' + ld_library_path

    if trace is False:
        trace = 0
    elif trace == 'basic' or trace is True:
        trace = 1
    elif trace == 'advanced':
        trace = 2
    else:
        print 'ERROR: Wrong tracing parameter ( [ True | basic ] | advanced | False)'
        return -1

    global graphing
    graphing = graph
    global tracing
    tracing = trace
    global monitoring
    monitoring = monitor

    exportGlobals()

    print "******************************************************"
    print "*************** PyCOMPSs Interactive *****************"
    print "******************************************************"
    print "*          .-~~-.--.                ____       __    *"
    print "*         :         )              |___ \     /  |   *"
    print "*   .~ ~ -.\       /.- ~~ .          __) |     | |   *"
    print "*   >       \`.   .'       <        / __/   _  | |   *"
    print "*  (         .- -.         )       |_____| |_| |_|   *"
    print "*   \`- -.-~  \`- -'  ~-.- -'                        *"
    print "*     (        :        )           _ _ .-:          *"
    print "*      ~--.    :    .--~        .-~  .-~  }          *"
    print "*          ~-.-^-.-~ \_      .~  .-~   .~            *"
    print "*                   \ \ '     \ '_ _ -~              *"
    print "*                    \`.\`.    //                    *"
    print "*           . - ~ ~-.__\`.\`-.//                     *"
    print "*       .-~   . - ~  }~ ~ ~-.~-.                     *"
    print "*     .' .-~      .-~       :/~-.~-./:               *"
    print "*    /_~_ _ . - ~                 ~-.~-._            *"
    print "*                                     ~-.<           *"
    print "******************************************************"

    ##############################################################
    # INITIALIZATION
    ##############################################################

    # Build a dictionary with all variables needed for initializing the runtime.
    config = {}
    config['compss_home'] = compss_home
    config['debug'] = debug
    if project_xml is None:
        config['project_xml'] = compss_home + os.path.sep + 'Runtime/configuration/xml/projects/default_project.xml'
    else:
        config['project_xml'] = project_xml
    if resources_xml is None:
        config['resources_xml'] = compss_home + os.path.sep + 'Runtime/configuration/xml/resources/default_resources.xml'
    else:
        config['resources_xml'] = resources_xml
    config['summary'] = summary
    config['taskExecution'] = taskExecution
    config['storageConf'] = storageConf
    config['taskCount'] = taskCount
    if appName is None:
        config['appName'] = 'Interactive'
    else:
        config['appName'] = appName
    config['uuid'] = uuid
    config['baseLogDir'] = baseLogDir
    config['specificLogDir'] = specificLogDir
    config['graph'] = graph
    config['monitor'] = monitor
    config['trace'] = trace
    config['extraeCfg'] = extraeCfg
    config['comm'] = comm
    config['conn'] = conn
    config['masterName'] = masterName
    config['masterPort'] = masterPort
    config['scheduler'] = scheduler
    config['cp'] = cp
    config['classpath'] = classPath
    config['jvmWorkers'] = jvmWorkers
    config['pythonPath'] = pythonPath
    config['cpuAffinity'] = cpuAffinity
    config['gpuAffinity'] = gpuAffinity

    initialize_compss(config)

    ##############################################################
    # RUNTIME START
    ##############################################################

    print "* - Starting COMPSs runtime...                       *"
    compss_start()

    if o_c is True:
        # set cross-module variable
        binding.object_conversion = True
    else:
        # set cross-module variable
        binding.object_conversion = False

    # Enable or disable the use of mmap
    # serializer.mmap_file_storage = False
    # Remove launch.py, log_level and object_conversion from sys.argv,
    # It will be inherited by the app through execfile
    # sys.argv = sys.argv[3:]
    # Get application execution path
    # app_path = sys.argv[0]  ############ not needed --> interactive mode

    global log_path
    log_path = get_log_path()
    binding.temp_dir = mkdtemp(prefix='pycompss', dir=log_path + '/tmpFiles/')
    print "* - Log path : " + log_path

    # Logging setup
    if log_level == "debug":
        init_logging(os.getenv('COMPSS_HOME') + '/Bindings/python/log/logging.json.debug', log_path)
    elif log_level == "info":
        init_logging(os.getenv('COMPSS_HOME') + '/Bindings/python/log/logging.json.off', log_path)
    elif log_level == "off":
        init_logging(os.getenv('COMPSS_HOME') + '/Bindings/python/log/logging.json.off', log_path)
    else:
        # Default
        init_logging(os.getenv('COMPSS_HOME') + '/Bindings/python/log/logging.json', log_path)
    logger = logging.getLogger("pycompss.runtime.launch")

    printSetup(verbose,
               log_level, o_c, debug, graph, trace, monitor,
               project_xml, resources_xml, summary, taskExecution, storageConf,
               taskCount, appName, uuid, baseLogDir, specificLogDir, extraeCfg,
               comm, conn, masterName, masterPort, scheduler, jvmWorkers)

    logger.debug("--- START ---")
    logger.debug("PyCOMPSs Log path: %s" % log_path)
    if storageConf is not None:
        logger.debug("Storage configuration file: %s" % storageConf)
        from storage.api import init as initStorage
        initStorage(config_file_path=storageConf)
        global persistent_storage
        persistent_storage = True

    # MAIN EXECUTION
    # let the user write an interactive application
    print "* - PyCOMPSs Runtime started... Have fun!            *"
    print "******************************************************"


def printSetup(verbose, log_level, o_c, debug, graph, trace, monitor,
          project_xml, resources_xml, summary, taskExecution, storageConf,
          taskCount, appName, uuid, baseLogDir, specificLogDir, extraeCfg,
          comm, conn, masterName, masterPort, scheduler, jvmWorkers):
    logger = logging.getLogger("pycompss.runtime.launch")
    output = ""
    output += "******************************************************\n"
    output += " CONFIGURATION: \n"
    output += "  - Log level         : " + str(log_level) + "\n"
    output += "  - Object conversion : " + str(o_c) + "\n"
    output += "  - Debug             : " + str(debug) + "\n"
    output += "  - Graph             : " + str(graph) + "\n"
    output += "  - Trace             : " + str(trace) + "\n"
    output += "  - Monitor           : " + str(monitor) + "\n"
    output += "  - Project XML       : " + str(project_xml) + "\n"
    output += "  - Resources XML     : " + str(resources_xml) + "\n"
    output += "  - Summary           : " + str(summary) + "\n"
    output += "  - Task execution    : " + str(taskExecution) + "\n"
    output += "  - Storage conf.     : " + str(storageConf) + "\n"
    output += "  - Task count        : " + str(taskCount) + "\n"
    output += "  - Application name  : " + str(appName) + "\n"
    output += "  - UUID              : " + str(uuid) + "\n"
    output += "  - Base log dir.     : " + str(baseLogDir) + "\n"
    output += "  - Specific log dir. : " + str(specificLogDir) + "\n"
    output += "  - Extrae CFG        : " + str(extraeCfg) + "\n"
    output += "  - COMM library      : " + str(comm) + "\n"
    output += "  - CONN library      : " + str(conn) + "\n"
    output += "  - Master name       : " + str(masterName) + "\n"
    output += "  - Master port       : " + str(masterPort) + "\n"
    output += "  - Scheduler         : " + str(scheduler) + "\n"
    output += "  - JVM Workers       : " + str(jvmWorkers) + "\n"
    output += "******************************************************"
    if verbose:
        print output
    logger.debug(output)


def stop(sync=False):
    print "******************************************************"
    print "**************** STOPPING PyCOMPSs *******************"
    print "******************************************************"

    logger = logging.getLogger("pycompss.runtime.launch")

    if sync:
        print "Synchronizing all future objects left on the user scope."
        logger.debug("Synchronizing all future objects left on the user scope.")
        from pycompss.api.api import compss_wait_on
        pending_to_synchronize = get_pending_to_synchronize()

        ipython = globals()['__builtins__']['get_ipython']()
        # import pprint
        # pprint.pprint(ipython.__dict__, width=1)
        raw_code = ipython.__dict__['user_ns']
        for k in raw_code:
            objK = raw_code[k]
            obj_id = id(objK)
            if not k.startswith('_'):   # not internal objects
                if type(objK) == binding.Future:
                    print "Found a future object: ", str(k)
                    logger.debug("Found a future object: %s" % (k,))
                    ipython.__dict__['user_ns'][k] = compss_wait_on(objK)
                elif obj_id in pending_to_synchronize:
                    print "Found an object to synchronize: ", str(k)
                    logger.debug("Found an object to synchronize: %s" % (k,))
                    ipython.__dict__['user_ns'][k] = compss_wait_on(objK)
                else:
                    pass
    else:
        print "Warning: some of the variables used with PyCOMPSs may"
        print "         have not been brought to the master."

    if persistent_storage is True:
        from storage.api import finish as finishStorage
        finishStorage()

    compss_stop()

    cleanTempFiles()

    print "******************************************************"
    logger.debug("--- END ---")
    # os._exit(00)  # Explicit kernel restart # breaks Jupyter-notebook

    # --- Execution finished ---


def showCurrentGraph(fit=False):
    if graphing:
        return __showGraph(name='current_graph', fit=fit)
    else:
        print 'Oops! Graph is not enabled in this execution.'
        print '      Please, enable it by setting the graph flag when starting PyCOMPSs.'


def showCompleteGraph(fit=False):
    if graphing:
        return __showGraph(name='complete_graph', fit=fit)
    else:
        print 'Oops! Graph is not enabled in this execution.'
        print '      Please, enable it by setting the graph flag when starting PyCOMPSs.'


def __showGraph(name='complete_graph', fit=False):
    try:
        from graphviz import Source
    except ImportError:
        print 'Oops! graphviz is not available.'
        raise
    file = open(log_path + '/monitor/' + name + '.dot', 'r')
    text = file.read()
    if fit:
        try:
            # Convert to png and show full picture
            filename = log_path + '/monitor/' + name
            extension = 'png'
            import os
            if os.path.exists(filename + '.' + extension):
                os.remove(filename + '.' + extension)
            s = Source(text, filename=filename, format=extension)
            s.render()
            from IPython.display import Image
            image = Image(filename=filename + '.' + extension)
            return image
        except:
            print 'Oops! Failed rendering the graph.'
            raise
    else:
        return Source(text)


###################################################################################################
###################################################################################################
###################################################################################################


def exportGlobals():
    # Super ugly, but I see no other way to define the app_path across the interactive execution without
    # making the user to define it explicitly.
    # It is necessary to define only one app_path because of the two decorators need to access the same information.
    # if the file is created per task, the constraint will not be able to work.
    # Get ipython globals
    ipython = globals()['__builtins__']['get_ipython']()
    # import pprint
    # pprint.pprint(ipython.__dict__, width=1)
    # Extract user globals from ipython
    userGlobals = ipython.__dict__['ns_table']['user_global']
    # Inject app_path variable to user globals so that task and constraint decorators can get it.
    temp_app_filename = os.getcwd() + '/' + "InteractiveMode_" + str(time.strftime('%d%m%y_%H%M%S')) + '.py'
    userGlobals['app_path'] = temp_app_filename
    global app_path
    app_path = temp_app_filename


def cleanTempFiles():
    '''
    Remove any temporary files that may exist.
    Currently: app_path, which contains the file path where all interactive code required by the worker is.
    '''
    try:
        if os.path.exists(app_path):
            os.remove(app_path)
        if os.path.exists(app_path + 'c'):
            os.remove(app_path + 'c')
    except OSError:
        print "[ERROR] An error has occurred when cleaning temporary files."


###################################################################################################
###################################################################################################
###################################################################################################

'''
# Start PyCOMPSs as an independent process.
# Not working on Jupyter-notebook, but may be useful for future implementations.

def startP(log_level="off",
          o_c=False,
          debug=False,
          graph=False,
          trace=False,
          monitor=None,
          project_xml='/opt/COMPSs/Runtime/configuration/xml/projects/default_project.xml',
          resources_xml='/opt/COMPSs/Runtime/configuration/xml/resources/default_resources.xml',
          summary=False,
          taskExecution='compss',
          storageConf=None,
          taskCount=50,
          appName='Interactive',
          uuid=None,
          baseLogDir=None,
          specificLogDir=None,
          extraeCfg=None,
          comm='NIO',
          masterName='',
          masterPort='43000',
          scheduler='es.bsc.compss.scheduler.defaultscheduler.DefaultScheduler',
          jvmWorkers='-Xms1024m,-Xmx1024m,-Xmn400m'
          ):
    global running
    global process
    if running:
        print "You have currently a running PyCOMPSs instance."
    else:
        print "[iPyCOMPSs] Starting process..."

        exportGlobals()

        process = Process(target=start, args=(log_level, o_c, debug, graph, trace, monitor,
                                              project_xml, resources_xml, summary, taskExecution,
                                              storageConf, taskCount, appName, uuid, baseLogDir,
                                              specificLogDir, extraeCfg, comm, masterName,
                                              masterPort, scheduler, jvmWorkers, True))
        process.daemon = True
        process.start()
        print "[iPyCOMPSs] Process started."
        running = True
'''

'''
# Stop PyCOMPSs process.
# Not working on Jupyter-notebook, but may be useful for future implementations.

def stopP(sync=False):
    # stopProcess(sync)
    global running
    global process
    if running:
        print "[iPyCOMPSs] Terminating process..."
        process.terminate()
        process = Process(target=stop, args=(sync))
        process.start()
        process.join()
        process.terminate()
        print "[iPyCOMPSs] Process terminated."
        running = False
    else:
        print "[iPyCOMPSs] There is not PyCOMPSs instance running."
'''
