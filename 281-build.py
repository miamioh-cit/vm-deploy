import time
from gns3fy import Gns3Connector, Project, Node, Link

# Manually add the new lab name and IP addresses for all machines, comma seperated.

LAB_NAME = "test-5"
IP_ADDRS = [“10.48.229.96”, “10.48.229.88“, “10.48.229.67“, “10.48.229.57“, “10.48.229.54“, "10.48.229.68“, 1“0.48.229.76“, “10.48.229.52“, “10.48.229.51“, “10.48.229.65“, “10.48.229.85“, “10.48.229.89”, “10.48.229.92“, “10.48.229.87“, “10.48.229.86“, “10.48.229.84“, "10.48.229.82“, “10.48.229.81“, “10.48.229.61“, “10.48.229.62“, “10.48.229.74“, “10.48.229.73“, “10.48.229.72”, “10.48.229.78”, “10.48.229.48“]
GNS3_USER = "gns3"
GNS3_PW = "gns3"


for IP_ADD in IP_ADDRS:
#Add Server Credentials, IP Address and Make a Connection

    SERVER_URL = "http://" + IP_ADD + ":80"
    server = Gns3Connector(url=SERVER_URL, user=GNS3_USER, cred=GNS3_PW)

    # Verify connectivity by checking the server version
    print("Connecting to GNS3 server to verify uniqueness of Project name", server.get_version(), "at", SERVER_URL)

    #Verify that lab name is unique, then create a new project on the server.
    try:
        lab = server.create_project(name=LAB_NAME)
    except:
        print("=========================================================")
        print("Error: May not be a unique Lab Name!")
        print("=========================================================")
        from sys import exit
        exit()

    #If lab name is unique, confirm with user.
    print("-----------------------------------------------------------------------")
    print("Project name is unique, nodes are being created.")
    print("-----------------------------------------------------------------------")
    print("Please wait until script runs before entering the project in GNS3!")
    print("-----------------------------------------------------------------------")

    # Now open the project from the server
    lab = Project(name=LAB_NAME, connector=server)
    lab.get()
    lab.open()

    #Build Cloud
    lab.create_node(name='internet', template='Cloud', x='76', y='-76')

    #Create Switches
    lab.create_node(name='offsite-switch', template='Cisco IOSvL2 15.2.1', x='-33', y='-175')
    sw1=lab.get_node("offsite-switch")
    sw1.start()

    lab.create_node(name='ohio-switch', template='Cisco IOSvL2 15.2.1', x='-19', y='280')
    sw2=lab.get_node("ohio-switch")
    sw2.start()

    lab.create_node(name='ky-switch-1', template='Cisco IOSvL2 15.2.1', x='163', y='275')
    sw3=lab.get_node("ky-switch-1")
    sw3.start()

    lab.create_node(name='ky-switch-2', template='Cisco IOSvL2 15.2.1', x='334', y='275')
    sw4=lab.get_node("ky-switch-2")
    sw4.start()

    #*******Create and Start Windows 10 Clients*********

    #Create and Start Offsite Windows 10 Client
    lab.create_node(name='offsite-win10', template='Windows 10 w/ Edge', x='50', y='-300')
    win10_off=lab.get_node("offsite-win10")
    win10_off.start()

    #Create and Start Indiana Windows 10 Client No. 1
    lab.create_node(name='in-win10-01', template='Windows 10 w/ Edge', x='-188', y='-68')
    win10_oh1=lab.get_node("in-win10-01")
    win10_oh1.start()

    #Create and Start Ohio Windows 10 Client No. 1
    lab.create_node(name='ohio-win10-01', template='Windows 10 w/ Edge', x='-200', y='400')
    win10_oh1=lab.get_node("ohio-win10-01")
    win10_oh1.start()

    #Create and Start Ohio Windows 10 Client No. 2
    lab.create_node(name='ohio-win10-02', template='Windows 10 w/ Edge', x='-116', y='400')
    win10_oh2=lab.get_node("ohio-win10-02")
    win10_oh2.start()

    #Create and Start Ohio Windows 10 Client No. 3
    lab.create_node(name='ohio-win10-03', template='Windows 10 w/ Edge', x='-28', y='400')
    win10_oh3=lab.get_node("ohio-win10-03")
    win10_oh3.start()

    #Create and Start Kentucky Windows 10 Client No. 1
    lab.create_node(name='ky-win10-01', template='Windows 10 w/ Edge', x='129', y='400')
    win10_ky1=lab.get_node("ky-win10-01")
    win10_ky1.start()

    #Create and Start Kentucky Windows 10 Client No. 2
    lab.create_node(name='ky-win10-02', template='Windows 10 w/ Edge', x='208', y='400')
    win10_ky2=lab.get_node("ky-win10-02")
    win10_ky2.start()

    #Create and Start Kentucky Windows 10 Client No. 3
    lab.create_node(name='ky-win10-03', template='Windows 10 w/ Edge', x='285', y='400')
    win10_ky3=lab.get_node("ky-win10-03")
    win10_ky3.start()

    #Create and Start Kentucky Windows 10 Client No. 4
    lab.create_node(name='ky-win10-04', template='Windows 10 w/ Edge', x='367', y='400')
    win10_ky4=lab.get_node("ky-win10-04")
    win10_ky4.start()

    #Create and start Routers

    lab.create_node(name='in-edge', template='Cisco IOSv 15.5(3)M', x='-113', y='32')
    router0=lab.get_node("in-edge")
    router0.start()

    lab.create_node(name='offsite-router', template='Cisco IOSv 15.5(3)M', x='-37', y='-72')
    router1=lab.get_node("offsite-router")
    router1.start()

    lab.create_node(name='ky-edge', template='Cisco IOSv 15.5(3)M', x='46', y='24')
    router2=lab.get_node("ky-edge")
    router2.start()

    lab.create_node(name='ky-int', template='Cisco IOSv 15.5(3)M', x='149', y='96')
    router3=lab.get_node("ky-int")
    router3.start()

    lab.create_node(name='oh-edge', template='Cisco IOSv 15.5(3)M', x='-31', y='91')
    router4=lab.get_node("oh-edge")
    router4.start()

    lab.create_node(name='oh-int', template='Cisco IOSv 15.5(3)M', x='-31', y='192')
    router5=lab.get_node("oh-int")
    router5.start()

    #Create and Start Windows Server 2022 Servers

    lab.create_node(name='offsite-web', template='Windows Server 2022', x='-75', y='-300')
    winserver16_1=lab.get_node("offsite-web")
    winserver16_1.start()

    lab.create_node(name='ohio-web', template='Windows Server 2022', x='-172', y='183')
    winserver16_3=lab.get_node("ohio-web")
    winserver16_3.start()


    #Link the nodes
    lab.create_link("offsite-web", "Ethernet0", "offsite-switch", "Gi0/0")
    lab.create_link("offsite-win10", "NIC1", "offsite-switch", "Gi0/1")
    lab.create_link("offsite-switch", "Gi0/2", "offsite-router", "Gi0/0")
    lab.create_link("in-edge", "Gi0/0", "offsite-router", "Gi0/1")
    lab.create_link("ky-edge", "Gi0/0", "offsite-router", "Gi0/2")
    lab.create_link("ky-edge", "Gi0/1", "ky-int", "Gi0/1")
    lab.create_link("ky-edge", "Gi0/2", "oh-edge", "Gi0/0")
    lab.create_link("in-edge", "Gi0/1", "oh-edge", "Gi0/1")
    lab.create_link("oh-edge", "Gi0/2", "oh-int", "Gi0/0")
    lab.create_link("internet", "eth0", "ky-edge", "Gi0/3")
    lab.create_link("oh-int", "Gi0/1", "ohio-switch", "Gi0/0")
    lab.create_link("ohio-win10-01", "NIC1", "ohio-switch", "Gi0/1")
    lab.create_link("ohio-win10-02", "NIC1", "ohio-switch", "Gi0/2")
    lab.create_link("ohio-win10-03", "NIC1", "ohio-switch", "Gi0/3")
    lab.create_link("ohio-web", "Ethernet0", "oh-int", "Gi0/2")
    lab.create_link("in-win10-01", "NIC1", "in-edge", "Gi0/2")
    lab.create_link("ky-int", "Gi0/0", "ky-switch-1", "Gi0/0")
    lab.create_link("ky-switch-1", "Gi0/1", "ky-switch-2", "Gi0/0")
    lab.create_link("ky-win10-01", "NIC1", "ky-switch-1", "Gi0/2")
    lab.create_link("ky-win10-02", "NIC1", "ky-switch-1", "Gi0/3")
    lab.create_link("ky-win10-03", "NIC1", "ky-switch-2", "Gi1/0")
    lab.create_link("ky-win10-04", "NIC1", "ky-switch-2", "Gi1/1")

    #Confirm completion of the script with the user.
    print("-----------------------------------------------------------------------")
    print("Nodes created, started and linked.")
    print("-----------------------------------------------------------------------")
    lab.links_summary()
    print("-----------------------------------------------------------------------")
    print(LAB_NAME + " build is Complete. It is now safe to open the project in GNS3")
    print("Be sure that you document the links in your Visio Topology!!!!")
    print("-----------------------------------------------------------------------")
