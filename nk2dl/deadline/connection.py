"""Deadline connection handling.

This module provides a unified interface for connecting to Deadline using either
the Web Service API or command-line interface.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from ..common.config import config
from ..common.errors import DeadlineError
from ..common.logging import logger

class DeadlineConnection:
    """Manages connection to Deadline.
    
    Provides a unified interface regardless of whether using Web Service
    or command-line interface.
    """
    
    def __init__(self):
        """Initialize connection based on configuration."""
        self.use_web_service = config.get('deadline.use_web_service', False)
        self._web_client = None
        self._command_path = None
        
        # Don't initialize connection in __init__ to make testing easier
        self._initialized = False
        
        # For command line, verify the command path exists - but only if we're using command line
        if not self.use_web_service:
            self._setup_command_line()
    
    def ensure_connected(self):
        """Ensure connection is initialized."""
        if not self._initialized:
            if self.use_web_service:
                self._init_web_service()
            else:
                self._init_command_line()
            self._initialized = True
    
    def _init_web_service(self) -> None:
        """Initialize web service connection."""
        try:
            from Deadline.DeadlineConnect import DeadlineCon as Connect
        except ImportError:
            if config.get('deadline.commandline_on_fail', True):
                logger.warning("Failed to import Deadline Web Service API. Attempting fallback to command line.")
                try:
                    self._setup_command_line()
                    self.use_web_service = False
                    self._init_command_line()
                    logger.info("Web Service connection failed. Successfully connected via command line.")
                    return
                except Exception as e:
                    logger.error("Web Service connection failed. Command line fallback also failed.")
                    raise DeadlineError(f"Failed to connect via both Web Service and command line: {e}")
            else:
                logger.error("Web Service connection failed. Command line fallback disabled in config.")
                raise DeadlineError(
                    "Failed to import Deadline Web Service API and fallback is disabled. "
                    "Enable fallback by setting deadline.commandline_on_fail=true in config."
                )
        
        host = config.get('deadline.host', 'localhost')
        port = config.get('deadline.port', 8081)
        use_ssl = config.get('deadline.ssl', False)
        ssl_cert = config.get('deadline.ssl_cert')
        
        try:
            if use_ssl:
                if not ssl_cert:
                    raise DeadlineError("SSL certificate path not provided. Please set NK2DL_DEADLINE_SSL_CERT environment variable.")
                if not os.path.exists(ssl_cert):
                    raise DeadlineError(f"SSL certificate not found at path: {ssl_cert}")
                
                # For PFX/P12 files, we don't need to verify the CA
                # The certificate itself contains the private key and certificate chain
                self._web_client = Connect(host, port, use_ssl, ssl_cert, False)
            else:
                # For non-SSL connections, only pass host and port
                self._web_client = Connect(host, port)
            
            # Test connection
            try:
                groups = self._web_client.Groups.GetGroupNames()
                if groups is None or not isinstance(groups, list):
                    raise DeadlineError(f"Invalid response from Groups.GetGroupNames(): {groups}")
                logger.info(f"Successfully connected to Deadline Web Service at {host}:{port}")
            except Exception as e:
                if config.get('deadline.commandline_on_fail', True):
                    logger.warning(f"Failed to test Deadline Web Service connection at {host}:{port}: {e}. Attempting fallback to command line.")
                    try:
                        self._setup_command_line()
                        self.use_web_service = False
                        self._init_command_line()
                        logger.info("Web Service connection failed. Successfully connected via command line.")
                        return
                    except Exception as fallback_error:
                        logger.error("Web Service connection failed. Command line fallback also failed.")
                        raise DeadlineError(f"Failed to connect via both Web Service and command line. Web Service error: {e}, Command line error: {fallback_error}")
                else:
                    logger.error("Web Service connection failed. Command line fallback disabled in config.")
                    raise DeadlineError(
                        f"Failed to connect to Deadline Web Service and fallback is disabled. "
                        f"Enable fallback by setting deadline.commandline_on_fail=true in config. Error: {e}"
                    )
        except Exception as e:
            if config.get('deadline.commandline_on_fail', True):
                logger.warning(f"Failed to connect to Deadline Web Service at {host}:{port}. Attempting fallback to command line.")
                try:
                    self._setup_command_line()
                    self.use_web_service = False
                    self._init_command_line()
                    logger.info("Web Service connection failed. Successfully connected via command line.")
                    return
                except Exception as fallback_error:
                    logger.error("Web Service connection failed. Command line fallback also failed.")
                    raise DeadlineError(f"Failed to connect via both Web Service and command line. Web Service error: {e}, Command line error: {fallback_error}")
            else:
                logger.error("Web Service connection failed. Command line fallback disabled in config.")
                raise DeadlineError(
                    f"Failed to connect to Deadline Web Service and fallback is disabled. "
                    f"Enable fallback by setting deadline.commandline_on_fail=true in config. Error: {e}"
                )
    
    def _init_command_line(self) -> None:
        """Initialize command-line interface."""
        # Test connection by getting repository path directly
        args = [self._command_path, "-GetRepositoryPath"]
        
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        try:
            proc = subprocess.Popen(
                args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo
            )
            output, errors = proc.communicate()
            
            if sys.version_info[0] > 2:
                output = output.decode()
            
            path = output.strip()
            if not path:
                raise DeadlineError("Empty repository path returned")
                
            logger.info("Successfully connected to Deadline via command-line")
            
        except Exception as e:
            raise DeadlineError(f"Failed to connect to Deadline: {e}")
    
    def get_groups(self) -> List[str]:
        """Get list of Deadline groups.
        
        Returns:
            List of group names
        """
        self.ensure_connected()
        
        if self.use_web_service:
            try:
                return self._web_client.Groups.GetGroupNames()
            except Exception as e:
                if config.get('deadline.commandline_on_fail', True):
                    logger.warning(f"Failed to get groups via web service: {e}. Falling back to command line.")
                    self._setup_command_line()
                    self.use_web_service = False
                    self._init_command_line()
                    return self.get_groups()  # Retry with command line
                else:
                    raise DeadlineError(f"Failed to get groups via web service: {e}")
        else:
            if "dotnet" in self._command_path:
                # For dotnet command string, split into command parts
                command_parts = self._command_path.split()
                command_parts.append("-Groups")
                args = command_parts
            else:
                args = [self._command_path, "-Groups"]
            try:
                proc = subprocess.Popen(
                    args,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                output, errors = proc.communicate()
                
                if sys.version_info[0] > 2:
                    output = output.decode()
                
                return [g.strip() for g in output.splitlines() if g.strip()]
            except Exception as e:
                raise DeadlineError(f"Failed to get groups: {e}")
    
    def submit_job(self, job_info: Dict[str, Any], plugin_info: Dict[str, Any]) -> str:
        """Submit a job to Deadline.
        
        Args:
            job_info: Job information dictionary
            plugin_info: Plugin-specific information dictionary
            
        Returns:
            Job ID
            
        Raises:
            DeadlineError: If job submission fails
        """
        self.ensure_connected()
        
        # Set UserName to current user if not specified
        if 'UserName' not in job_info:
            import getpass
            job_info['UserName'] = getpass.getuser()
        
        # Convert all values to strings
        def stringify_dict(d: Dict[str, Any]) -> Dict[str, str]:
            return {k: str(v) for k, v in d.items()}
        
        job_info_str = stringify_dict(job_info)
        plugin_info_str = stringify_dict(plugin_info)
        
        if self.use_web_service:
            # Submit via web service using direct JSON API
            logger.info(f"Submitting job via web service")

            try:
                import json
                
                # Create the payload as required by the Deadline REST API
                payload = {
                    "JobInfo": job_info_str,
                    "PluginInfo": plugin_info_str
                }
                
                # Log the JSON payload for debugging
                logger.info(f"Submitting job JSON payload:\n{json.dumps(payload, indent=2)}")
                
                # Submit job with correct arguments to the API
                job_response = self._web_client.Jobs.SubmitJob(job_info_str, plugin_info_str)
                
                if isinstance(job_response, str) and job_response.startswith("Error:"):
                    raise DeadlineError(f"Failed to submit job: {job_response}")
                
                # Extract job ID from response - handle both string and dict responses
                if isinstance(job_response, dict) and '_id' in job_response.get('Props', {}):
                    # Extract just the ID from the response dictionary
                    job_id = job_response['Props']['_id']
                elif isinstance(job_response, str):
                    job_id = job_response
                else:
                    # Try to find any ID property in the response
                    if isinstance(job_response, dict):
                        # Log the response for debugging
                        logger.debug(f"Retrieving job ID from response: {job_response}")
                        # Look for '_id' anywhere in the dictionary
                        if '_id' in job_response:
                            job_id = job_response['_id']
                            logger.debug(f"Found job ID in response: {job_id}")
                        else:
                            raise DeadlineError(f"Could not find job ID in response: {job_response}")
                    else:
                        raise DeadlineError(f"Unexpected job response format: {job_response}")
                
                logger.info(f"Job submitted successfully with ID: {job_id}")
                return job_id  # Return just the string ID
                
            except Exception as e:
                if config.get('deadline.commandline_on_fail', True):
                    logger.warning(f"Failed to submit job via web service: {e}. Falling back to command line.")
                    self._setup_command_line()
                    self.use_web_service = False
                    self._init_command_line()
                    return self.submit_job(job_info, plugin_info)  # Retry with command line
                else:
                    raise DeadlineError(f"Failed to submit job via web service: {e}")
        else:
            # Command line submission using files
            logger.info(f"Submitting job via deadline command line")

            import tempfile
            job_info_path = None
            plugin_info_path = None
            
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.job', delete=False) as job_file:
                    for key, value in job_info_str.items():
                        job_file.write(f"{key}={value}\n")
                    job_info_path = job_file.name
                    
                with tempfile.NamedTemporaryFile(mode='w', suffix='.job', delete=False) as plugin_file:
                    for key, value in plugin_info_str.items():
                        plugin_file.write(f"{key}={value}\n")
                    plugin_info_path = plugin_file.name
                
                # Log the files for debugging
                with open(job_info_path, 'r') as f:
                    job_data = f.read()
                with open(plugin_info_path, 'r') as f:
                    plugin_data = f.read()
                    
                logger.info(f"Submitting job info:\n{job_data}")
                logger.info(f"Submitting plugin info:\n{plugin_data}")
                
                # Submit via command line
                if "dotnet" in self._command_path:
                    # For dotnet command string, split into command parts
                    command_parts = self._command_path.split()
                    command_parts.extend([job_info_path, plugin_info_path])
                    args = command_parts
                else:
                    args = [self._command_path, job_info_path, plugin_info_path]
                
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                try:
                    proc = subprocess.Popen(
                        args,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        startupinfo=startupinfo
                    )
                    output, errors = proc.communicate()
                    
                    if sys.version_info[0] > 2:
                        output = output.decode()
                        if errors:
                            errors = errors.decode()
                    
                    # Check for errors
                    if errors and "error" in errors.lower():
                        raise DeadlineError(f"Command line error: {errors}")
                    
                    # Log the response for debugging
                    logger.debug(f"Retrieving job ID from response: {output}")
                    # Parse job ID from output
                    for line in output.splitlines():
                        if line.startswith("JobID="):
                            job_id = line[6:].strip()
                            logger.info(f"Job submitted successfully with ID: {job_id}")
                            return job_id
                            
                    raise DeadlineError("No job ID found in submission output")
                    
                except Exception as e:
                    raise DeadlineError(f"Failed to submit job via command line: {e}")
                    
            finally:
                # Clean up temporary files
                if job_info_path and os.path.exists(job_info_path):
                    try:
                        os.unlink(job_info_path)
                    except Exception as e:
                        logger.warning(f"Failed to clean up job info file {job_info_path}: {e}")
                if plugin_info_path and os.path.exists(plugin_info_path):
                    try:
                        os.unlink(plugin_info_path)
                    except Exception as e:
                        logger.warning(f"Failed to clean up plugin info file {plugin_info_path}: {e}")

    def _setup_command_line(self) -> None:
        """Set up command line path for fallback."""
        # Try to find it in DEADLINE_PATH
        deadline_bin = ""
        try:
            deadline_bin = os.environ['DEADLINE_PATH']
        except KeyError:
            # If the error is a key error it means that DEADLINE_PATH is not set
            pass
            
        # On OSX, we look for the DEADLINE_PATH file if the environment variable does not exist.
        if deadline_bin == "" and os.path.exists("/Users/Shared/Thinkbox/DEADLINE_PATH"):
            with open("/Users/Shared/Thinkbox/DEADLINE_PATH") as f:
                deadline_bin = f.read().strip()

        if deadline_bin:
            self._command_path = os.path.join(deadline_bin, "deadlinecommand")
            if sys.platform == 'win32':
                self._command_path += '.exe'
        
        if not self._command_path or not os.path.exists(self._command_path):
            raise DeadlineError(
                "Could not find deadlinecommand. Please ensure Deadline is installed "
                "and DEADLINE_PATH environment variable is set correctly."
            )

# Global connection instance - but don't initialize it yet
_connection = None

def get_connection() -> DeadlineConnection:
    """Get the global connection instance, creating it if needed."""
    global _connection
    if _connection is None:
        _connection = DeadlineConnection()
    return _connection 