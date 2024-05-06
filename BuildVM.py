import ssl
import re
import time
import ipaddress
from pyVmomi import vim, vmodl
from pyVim.connect import SmartConnect, Disconnect
from flask import flash

# Function to wait for a vSphere task to complete
def wait_for_task(task):
    while task.info.state == vim.TaskInfo.State.running:
        time.sleep(2)
    if task.info.state == vim.TaskInfo.State.success:
        return task.info.result
    else:
        raise Exception(f"Task error: {task.info.error}")

# Function to retrieve an object from vCenter
def get_obj(content, vimtype, name):
    obj = None
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    container.Destroy()  # Important to destroy the container view to free resources
    return obj
# Function to disable SSL certificate verification (useful in development environments)
def disable_ssl_verification():
    ssl._create_default_https_context = ssl._create_unverified_context

def connect_to_vcenter(vcenter_ip, vcenter_user, vcenter_password):
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
        si = SmartConnect (host=vcenter_ip, user=vcenter_user, pwd=vcenter_password, port=443)
        return si
    except vim.fault.InvalidLogin as invalid_login:
        print("Invalid login credentials")
        return None
    except Exception as e:
        print(f"Failed to connect to vCenter: {e}")
        return None

# Function to disconnect from vCenter
def disconnect_from_vcenter(si):
    Disconnect(si)

def reset_vm_by_name(si, vm_name):
    try:
        content = si.RetrieveContent()
        vm = get_obj(content, [vim.VirtualMachine], vm_name)
        if vm:
            reset_task = vm.ResetVM_Task()
            wait_for_task(reset_task)
            for _ in range(60):  # Timeout after 300 seconds
                time.sleep(5)
                vm.Reload()  # Reload the VM object to get the latest properties
                if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn and vm.guest.ipAddress:
                    flash(f"VM {vm_name} is back online with IP {vm.guest.ipAddress}. DO NOT TRY TO RESET YOUR VM FOR THE NEXT 10 MINUTES TO AVOID CORRUPTION!", "success")
                    break
            else:
                flash(f"Timeout waiting for VM {vm_name} to come back online.", "error")
        else:
            flash(f"VM {vm_name} not found.", "error")
    except vmodl.MethodFault as error:
        flash(f"Error resetting VM {vm_name}: {error.msg}", "error")
    except Exception as error:
        flash(f"General error when attempting to reset VM {vm_name}: {error}", "error")

# Function to get all VMs in vCenter
def get_all_vms(content):
    vm_list = []
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
    for c in container.view:
        vm_list.append(c)
    container.Destroy()
    return vm_list

# Function to search for VMs based on the username extracted from an email address
def search_user_vms(vcenter_ip, vcenter_user, vcenter_password, email):
    # Extract username from email address
    username = email.split('@')[0]

    # Connect to vCenter with provided credentials
    si = connect_to_vcenter(vcenter_ip, vcenter_user, vcenter_password)
    if si is None:
        # Return error message if connection fails
        return "Invalid credentials"

    try:
        content = si.RetrieveContent()
        # Retrieve all VMs visible to the user
        all_vms = get_all_vms(content)
        # Filter VMs by those starting with the username
        user_vms = [vm for vm in all_vms if vm.name.startswith(username)]

        if not user_vms:
            # No VMs found for user, disconnect and return message
            Disconnect(si)
            return "No VMs found for the specified user."

        vm_details = []
        for vm in user_vms:
            # Initialize IP addresses
            ipv4_address = None
            ipv6_address = None
            # Check network information for each VM
            for net_info in vm.guest.net:
                for ip in net_info.ipConfig.ipAddress:
                    if ipaddress.ip_address(ip.ipAddress).version == 4:
                        ipv4_address = ip.ipAddress
                        break  # Prefer IPv4 address
                    elif ipaddress.ip_address(ip.ipAddress).version == 6 and not ipv6_address:
                        ipv6_address = ip.ipAddress  # Fallback to IPv6
            chosen_ip = ipv4_address if ipv4_address else ipv6_address
            if not chosen_ip:
                chosen_ip = "IP address not available"
            # Determine the power state of the VM
            vm_power_state = "On" if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn else "Off"
            # Append VM details including power state
            vm_details.append(f"{vm.name}: {chosen_ip}: {vm_power_state}")

        # Format the VM information string
        vm_info_str = "\n".join(vm_details)
        # Disconnect from vCenter after retrieval
        Disconnect(si)
        return vm_info_str  # Return the VM details including power state
    except Exception as e:
        print(f"Error during VM search: {e}")
        # Ensure disconnection on error
        Disconnect(si)
        return "An error occurred while searching for VMs."
    
import re  # Import the re module for regex operations

def power_on_vm_by_name(si, vm_name):
    try:
        content = si.RetrieveContent()
        vm = get_obj(content, [vim.VirtualMachine], vm_name)
        if vm:
            if vm.runtime.powerState != vim.VirtualMachinePowerState.poweredOn:
                power_on_task = vm.PowerOnVM_Task()  # Initiates power on task
                wait_for_task(power_on_task)  # Wait for the power on task to complete
                # Wait for IP address to be assigned to the VM
                for _ in range(60):  # Wait up to 5 minutes for an IP address
                    time.sleep(5)  # Check every 5 seconds
                    vm.Reload()  # Reload the VM object to get the latest properties
                    ip_address = vm.guest.ipAddress
                    if ip_address:
                        return True, ip_address  # Return success and IP address
                return True, "IP address not available"  # Powered on but no IP after timeout
            else:
                print(f"VM {vm_name} is already powered on.")
                ip_address = vm.guest.ipAddress
                return False, ip_address if ip_address else "IP address not available"  # Already on, return IP if available
        else:
            print(f"VM {vm_name} not found.")
            return False, None  # VM not found
    except Exception as e:
        print(f"Failed to power on VM {vm_name}: {e}")
        return False, None  # Error during power on

def clone_and_configure_vm(content, vm_template_name, username, class_option, datacenter_name):
    # Expanded class prefixes for all class options, including specific courses and capstone projects
    class_prefix_map = {
        'CIT281': 'CIT281',
        'CIT284': 'CIT284',
        'CIT358': 'CIT358',
        'CIT386': 'CIT386',
        'CIT480': 'CIT480',
        'Windows Capstone': 'CP-W',
        'Linux Capstone': 'CP-L',
    }
    # Use class prefix based on class_option; default to the class_option itself if not found
    class_prefix = class_prefix_map.get(class_option, class_option)

    # Update base VM name according to the new naming convention
    vm_base_name = f"{username}-{class_prefix}"

    # Retrieve all existing VMs to check for existing VMs for this user and class
    existing_vms = get_all_vms(content)
    
    # Filter VMs by the new naming convention, considering both username and class prefix
    user_class_vms = [vm for vm in existing_vms if vm.name.startswith(vm_base_name)]

    # Determine the number of VMs allowed based on class option
    max_vms_allowed = 3 if class_option in ['Windows Capstone', 'Linux Capstone'] else 1

    # Calculate existing count accurately for the specific class
    existing_count = len(user_class_vms)
    
    if existing_count >= max_vms_allowed:
        # Use regex to extract the numeric part for sorting
        def extract_number(vm_name):
            match = re.search(r'\d+$', vm_name)  # Finds one or more digits at the end of the string
            return int(match.group()) if match else 0  # Convert to int if found, else default to 0

        sorted_vms = sorted(user_class_vms, key=lambda vm: extract_number(vm.name))
        
        # Initialize a list to hold formatted VM information (name and IP)
        vm_details = []
        for vm in sorted_vms:
            ip_address = vm.guest.ipAddress if vm.guest.ipAddress else "IP address not available"
            vm_details.append(f"{vm.name}: {ip_address}")
        
        # Format the VM information string
        vm_info_str = "<br>".join(vm_details)
        return f"Sorry, but it looks like you already have the maximum number of machines ({max_vms_allowed}) made for that class. Here are the IP address(es) for your existing machine(s):<br>{vm_info_str}"

    # VM naming with incremented count
    vm_clone_name = f"{vm_base_name}-{existing_count + 1}"

    # Get the VM template
    vm_template = get_obj(content, [vim.VirtualMachine], vm_template_name)
    if not vm_template:
        print(f"VM template {vm_template_name} not found!")
        return None

    # Specify where to place the cloned VM
    datacenter = get_obj(content, [vim.Datacenter], datacenter_name)
    resource_pool = datacenter.hostFolder.childEntity[0].resourcePool

    # Clone specs of the base VM
    clone_spec = vim.vm.CloneSpec(
        powerOn=True,
        template=False,
        location=vim.vm.RelocateSpec(pool=resource_pool)
    )

    # Proceed to clone the VM
    print(f"Cloning {vm_template_name} to {vm_clone_name}...")
    clone_task = vm_template.Clone(name=vm_clone_name, folder=datacenter.vmFolder, spec=clone_spec)
    wait_for_task(clone_task)

    # After cloning, return the cloned VM object for IP retrieval
    cloned_vm = get_obj(content, [vim.VirtualMachine], vm_clone_name)
    if cloned_vm:
        print(f"Successfully cloned VM: {cloned_vm.name}")
        return cloned_vm  # Return the cloned VM object
    else:
        return None  # In case cloning fails, return None

# Main function updated to use class options instead of direct Windows/Linux selection
def main(vcenter_ip, vcenter_user, vcenter_password, class_option, datacenter_name, username):
    # Map class options to specific VM templates
    class_to_template_map = {
        'CIT281': 'GNS3 VM',
        'CIT284': 'GNS3 VM',
        'CIT358': 'GNS3 VM',
        'CIT386': 'GNS3 VM',
        'CIT480': 'GNS3 VM',
        'Windows Capstone': 'Windows Server 2022 (Hunterds SP)',
        'Linux Capstone': 'Ubuntu 22.04 (Hunterds SP)'
    }

    template = class_to_template_map.get(class_option, 'Windows Server 2022 (Hunterds SP)')  # Default to Windows if not found

    # Disable SSL verification due to invalid certificate
    ssl._create_default_https_context = ssl._create_unverified_context

    # Attempt to connect to vCenter and handle invalid credentials
    try:
        si = SmartConnect (host=vcenter_ip, user=vcenter_user, pwd=vcenter_password, port=443)
    except vim.fault.InvalidLogin as e:
        print("Invalid login credentials.")
        return "Invalid credentials"
    except Exception as e:
        print(f"Failed to connect to vCenter: {e}")
        return "An error occurred while connecting to vCenter"

    content = si.RetrieveContent()

    # Attempt to clone or find an existing VM
    cloned_vm_or_ip = clone_and_configure_vm(content, template, username, class_option, datacenter_name)

    if cloned_vm_or_ip:
        if isinstance(cloned_vm_or_ip, str):  # An IP address was returned, indicating an existing VM
            print(f"Operation completed. The IP address of your VM is: {cloned_vm_or_ip}")
            ip_address = cloned_vm_or_ip
        else:  # A VM object was returned, indicating a new VM was successfully cloned
            print(f"Successfully cloned VM: {cloned_vm_or_ip.name}")
            # Wait for the VM to obtain an IP address
            print(f"Waiting for {cloned_vm_or_ip.name} to get an IP address...")
            ip_address = None
            wait_time = 0
            max_wait_time = 300  # Maximum wait time in seconds
            while not ip_address and wait_time < max_wait_time:
                time.sleep(5)  # Check every 5 seconds
                cloned_vm_or_ip = get_obj(content, [vim.VirtualMachine], cloned_vm_or_ip.name)  # Refresh VM object
                ip_address = cloned_vm_or_ip.guest.ipAddress
                wait_time += 5

            if ip_address:
                print(f"{cloned_vm_or_ip.name} IP Address: {ip_address}")
            else:
                print(f"Failed to obtain an IP address for {cloned_vm_or_ip.name} within the timeout period.")
                ip_address = "IP address not available"
    else:
        print("Failed to clone or find an existing VM.")
        ip_address = None

    # Disconnect from vCenter if not already disconnected
    Disconnect(si)
    return ip_address  # Return the IP address or None if the operation was unsuccessful

if __name__ == "__main__":
    port = int(os.environ.get(“PORT”, 5000))
    app.run(debug=True, host=‘0.0.0.0’, port=port)
