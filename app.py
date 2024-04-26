from flask import Flask, render_template, request, redirect, url_for, flash, session
from BuildVM import search_user_vms, main, reset_vm_by_name, connect_to_vcenter, disconnect_from_vcenter, power_on_vm_by_name  # Import the required functions

app = Flask(__name__)
app.secret_key = '3fa45b4d6f2c4b9ed9e3c1f86f2b2c3d'

@app.route('/', methods=['GET', 'POST'])
def index():
    # Initialize an error message variable for the template
    error_message = None
    if request.method == 'POST':
        # Retrieve form data from the request
        vcenter_user = request.form.get('vcenter_user')
        vcenter_password = request.form.get('vcenter_password')
        class_option = request.form.get('class_option')

        # Extract the username from the vcenter_user input
        username = vcenter_user.split('@')[0] if vcenter_user else ''

        # Define hardcoded values for vCenter IP and Datacenter Name
        vcenter_ip = "10.48.10.200"
        datacenter_name = "CIT Datacenter"

        # Call the main function with the collected inputs
        result = main(vcenter_ip, vcenter_user, vcenter_password, class_option, datacenter_name, username)

        # Handle the return value from main function for different scenarios
        if result == "Invalid credentials":
            error_message = "Invalid credentials to create VM's. Please check your username and password."
        elif "already have the maximum number of machines" in result:
            return redirect(url_for('success', message=result))
        elif result:
            return redirect(url_for('success', message=f"Operation completed successfully. The IP address of your new VM is: {result}"))
        else:
            error_message = "An error occurred. Unable to create or retrieve information for a VM."


    return render_template('index.html', error_message=error_message)

@app.route('/success')
def success():
    # Retrieve the message from the query string of the redirected request
    message = request.args.get('message', 'Unknown status')
    # Pass the message directly to the template for display
    return render_template('success.html', message=message)


@app.route('/search_vms', methods=['GET', 'POST'])
def search_vms():
    vcenter_ip = "10.48.10.200"
    if request.method == 'POST':
        vcenter_user = request.form.get('vcenter_user', '')
        vcenter_password = request.form.get('vcenter_password', '')
        session['vcenter_user'] = vcenter_user
        session['vcenter_password'] = vcenter_password
    else:
        vcenter_user = session.get('vcenter_user', '')
        vcenter_password = session.get('vcenter_password', '')

    if vcenter_user and vcenter_password:
        vms_info = search_user_vms(vcenter_ip, vcenter_user, vcenter_password, vcenter_user)
        if vms_info == "Invalid credentials":
            return render_template('index.html', error_message="Invalid credentials. Please check your username and password.")
        elif isinstance(vms_info, str) and (vms_info.startswith("No VMs found") or vms_info.startswith("An error occurred")):
            return render_template('index.html', error_message=vms_info)
        else:
            vms_info_list = [tuple(info.split(': ')) for info in vms_info.split('\n') if info]
            vms_info_sorted = sorted(vms_info_list, key=lambda x: x[0])
            return render_template('vm_search_results.html', vms_info=vms_info_sorted)
    else:
        return render_template('index.html', error_message="Missing vCenter username or password")

@app.route('/reset_vm', methods=['POST'])
def reset_vm():
    vm_name = request.form['vm_name']
    # Retrieve vCenter credentials from session
    vcenter_ip = "10.48.10.200"
    vcenter_user = session.get('vcenter_user')
    vcenter_password = session.get('vcenter_password')
    
    if not vcenter_user or not vcenter_password:
        flash('vCenter credentials not found. Please log in again.', 'error')
        return redirect(url_for('index'))
    
    si = connect_to_vcenter(vcenter_ip, vcenter_user, vcenter_password)
    if si:
        reset_vm_by_name(si, vm_name)
        disconnect_from_vcenter(si)
        return redirect(url_for('search_vms'))  # Redirect to the VM search page to show the message
    else:
        flash('Failed to connect to vCenter to reset VM.', 'error')
        return redirect(url_for('index'))
    
@app.route('/power_on_vm', methods=['POST'])
def power_on_vm():
    vm_name = request.form.get('vm_name')
    # Retrieve vCenter credentials from session
    vcenter_ip = "10.48.10.200"  # Use stored IP or a constant if applicable
    vcenter_user = session.get('vcenter_user')
    vcenter_password = session.get('vcenter_password')

    # Check for presence of vCenter credentials
    if not vcenter_user or not vcenter_password:
        flash('vCenter credentials not found. Please log in again.', 'error')
        return redirect(url_for('search_vms'))

    # Connect to vCenter
    si = connect_to_vcenter(vcenter_ip, vcenter_user, vcenter_password)
    if si:
        success, ip_address = power_on_vm_by_name(si, vm_name)  
        if success:
            # If VM powered on successfully, flash success message with IP address
            flash(f'VM powered on successfully. IP: {ip_address}. DO NOT TRY TO RESET YOUR VM FOR THE NEXT 10 MINUTES TO AVOID CORRUPTION! ', 'success')
        else:
            # If failed to power on VM, flash error message
            flash('Failed to power on VM. It may already be on or does not exist.', 'error')
        # Disconnect from vCenter after operation
        disconnect_from_vcenter(si)
    else:
        # If failed to connect to vCenter, flash error message
        flash('Failed to connect to vCenter.', 'error')

    # Redirect back to VM search results page
    return redirect(url_for('search_vms'))

if __name__ == '__main__':
    # Run the Flask application in debug mode for development purposes
    app.run(debug=True)
