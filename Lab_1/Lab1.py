# -*-  Mode: Python; -*-
# /*
#  * This program is free software; you can redistribute it and/or modify
#  * it under the terms of the GNU General Public License version 2 as
#  * published by the Free Software Foundation;
#  *
#  * This program is distributed in the hope that it will be useful,
#  * but WITHOUT ANY WARRANTY; without even the implied warranty of
#  * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  * GNU General Public License for more details.
#  *
#  * You should have received a copy of the GNU General Public License
#  * along with this program; if not, write to the Free Software
#  * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#  *
#  * Ported to Python by Mohit P. Tahiliani
#  */
# Reference Taken from /it/kurs/datakom2/bake/source/ns-3.36/examples/tutorial/second.py
# Edited for Lab in Computer Networks 1DT074 2 By
# Siva Shankar Siva Saravanan   & Siriwardanage Don Supun Madusanka
# Execute : ./ns3-run Lab1.py

# About CSMA for a Ring Topology with Three Nodes

# // Ring Network Topology
# // +----------+
# // |          |
# // n0----n1----n2


# Import ns-3 modules
import ns.core
import ns.network
import ns.csma
import ns.internet
import ns.applications
import sys

# Set up command line arguments
cmd = ns.core.CommandLine()
cmd.nCsma = 3
cmd.verbose = "True"
cmd.AddValue("nCsma", "Number of CSMA nodes")
cmd.AddValue("verbose", "Tell echo applications to log if true")
cmd.Parse(sys.argv)

# Get the number of CSMA nodes and verbose mode from command line arguments
nCsma = int(cmd.nCsma)
verbose = cmd.verbose

# Enable logging if in verbose mode
if verbose == "True":
    ns.core.LogComponentEnable("UdpEchoClientApplication", ns.core.LOG_LEVEL_INFO)
    ns.core.LogComponentEnable("UdpEchoServerApplication", ns.core.LOG_LEVEL_INFO)

# Create CSMA nodes
csmaNodes = ns.network.NodeContainer()
csmaNodes.Create(nCsma)

# Create CSMA helper and set channel attributes
csma = ns.csma.CsmaHelper()
csma.SetChannelAttribute("DataRate", ns.core.StringValue("100Mbps"))
csma.SetChannelAttribute("Delay", ns.core.TimeValue(ns.core.NanoSeconds(6560)))

# Install CSMA devices on nodes
csmaDevices = csma.Install(csmaNodes)

# Install internet stack on nodes
stack = ns.internet.InternetStackHelper()
stack.Install(csmaNodes)

# Assign IP addresses to CSMA devices
address = ns.internet.Ipv4AddressHelper()
address.SetBase(ns.network.Ipv4Address("10.1.1.0"), ns.network.Ipv4Mask("255.255.255.0"))
csmaInterfaces = address.Assign(csmaDevices)

# Create UdpEchoServer and install on the first CSMA node
echoServer = ns.applications.UdpEchoServerHelper(9)
serverApps = echoServer.Install(csmaNodes.Get(0))
serverApps.Start(ns.core.Seconds(1.0))
serverApps.Stop(ns.core.Seconds(30.0))

# Create UdpEchoClient and install on the last CSMA node
echoClient = ns.applications.UdpEchoClientHelper(csmaInterfaces.GetAddress(nCsma - 1), 9)
echoClient.SetAttribute("MaxPackets", ns.core.UintegerValue(1))
echoClient.SetAttribute("Interval", ns.core.TimeValue(ns.core.Seconds(1.0)))
echoClient.SetAttribute("PacketSize", ns.core.UintegerValue(1024))

clientApps = echoClient.Install(csmaNodes.Get(nCsma - 1))
clientApps.Start(ns.core.Seconds(2.0))
clientApps.Stop(ns.core.Seconds(30.0))

# Enable pcap tracing on the second CSMA device
csma.EnablePcap("Ring_CSMA", csmaDevices.Get(0), True)
csma.EnablePcap("Ring_CSMA", csmaDevices.Get(1), True)
csma.EnablePcap("Ring_CSMA", csmaDevices.Get(2), True)

# Run the simulation
ns.core.Simulator.Run()
ns.core.Simulator.Destroy()
