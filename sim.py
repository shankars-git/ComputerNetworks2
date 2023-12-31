##################################
# This contains following topology
#
#        10.1.1.0                       10.1.3.0
#  n0 -------------- n1    n2   n3 --------------- n4
#     point-to-point  |     |    |  point-to-point
#           N1        ============        N2
#                     LAN 10.1.2.0
##################################

import ns.core
import ns.network
import ns.csma
import ns.internet
import ns.point_to_point
import ns.applications
import ns.flow_monitor
import sys

#######################################################################################
# SEEDING THE RNG
#
# Enable this line to have random number being generated between runs.

#ns.core.RngSeedManager.SetSeed(int(time.time() * 1000 % (2**31-1)))

# command line inputs and other global parameters
cmd = ns.core.CommandLine()
cmd.nCsma       = 3
cmd.p2pLatency  = 1
cmd.p2pRate     = "5Mbps"
cmd.on_off_rate = 300000
cmd.interval    = 0.001
cmd.verbose     = "True"
cmd.AddValue("nCsma", "Number of CSMA nodes/devices")
cmd.AddValue("verbose", "Tell echo applications to log if true")
cmd.AddValue("p2pRate", "P2P data rate as a string")
cmd.AddValue("p2pLatency", "P2P link Latency in miliseconds")
cmd.AddValue("on_off_rate", "OnOffApplication data sending rate")
cmd.AddValue("interval", "UDP client packet interval")
cmd.Parse(sys.argv)

# Create LAN nodes
csmaNodes = ns.network.NodeContainer()
csmaNodes.Create(cmd.nCsma)

# Create point-to-point nodes in N1
n0n1 = ns.network.NodeContainer()
n0n1.Create(1)
n0n1.Add(csmaNodes.Get(0))

# Create point-to-point nodes in N1
n4n3 = ns.network.NodeContainer()
n4n3.Create(1)
n4n3.Add(csmaNodes.Get(2))

# UDP clients
udpClientNode = ns.network.NodeContainer()
udpClientNode.Add(n0n1.Get(0))

# UDP clients
udpServerNode = ns.network.NodeContainer()
udpServerNode.Add(csmaNodes.Get(1))

# point-to-point declaration and attribute setup
pointToPoint = ns.point_to_point.PointToPointHelper()
pointToPoint.SetDeviceAttribute("DataRate", ns.core.StringValue(cmd.p2pRate))
pointToPoint.SetChannelAttribute("Delay", 
                                ns.core.TimeValue(ns.core.MilliSeconds(int(cmd.p2pLatency))))
# Install NIC
d0d1 = pointToPoint.Install(n0n1)
d4d3 = pointToPoint.Install(n4n3)

# CSMA nodes declaration and attribute setup
csma = ns.csma.CsmaHelper()
csma.SetChannelAttribute("DataRate", ns.core.StringValue("10Mbps"))
csma.SetChannelAttribute("Delay", ns.core.TimeValue(ns.core.NanoSeconds(6560)))
# Install NIC
csmaDevices = csma.Install(csmaNodes)

# Enable error model
em = ns.network.RateErrorModel()
em.SetAttribute("ErrorUnit", ns.core.StringValue("ERROR_UNIT_PACKET"))
em.SetAttribute("ErrorRate", ns.core.DoubleValue(0.02))
d0d1.Get(1).SetReceiveErrorModel(em)

#######################################################################################
# CONFIGURE TCP
#
# Choose a TCP version and set some attributes.

# Set a TCP segment size (this should be inline with the channel MTU)
ns.core.Config.SetDefault("ns3::TcpSocket::SegmentSize", ns.core.UintegerValue(1448))

# If you want, you may set a default TCP version here. It will affect all TCP
# connections created in the simulator. If you want to simulate different TCP versions
# at the same time, see below for how to do that.
#ns.core.Config.SetDefault("ns3::TcpL4Protocol::SocketType",
#                          ns.core.StringValue("ns3::TcpTahoe"))
#                          ns.core.StringValue("ns3::TcpReno"))
#                          ns.core.StringValue("ns3::TcpLinuxReno"))
#                          ns.core.StringValue("ns3::TcpWestwood"))

# Some examples of attributes for some of the TCP versions.
#ns.core.Config.SetDefault("ns3::TcpLinuxReno::ReTxThreshold", ns.core.UintegerValue(4))
ns.core.Config.SetDefault("ns3::TcpWestwood::ProtocolType",
                          ns.core.StringValue("WestwoodPlus"))

# Install the internet stack on nodes
stack = ns.internet.InternetStackHelper()
stack.Install(n0n1.Get(0))
stack.Install(n4n3.Get(0))
stack.Install(csmaNodes)

# Assign IPV4 addresses for nodes
address = ns.internet.Ipv4AddressHelper()
address.SetBase(ns.network.Ipv4Address("10.1.1.0"), ns.network.Ipv4Mask("255.255.255.0"))
if0if1 = address.Assign(d0d1)

address.SetBase(ns.network.Ipv4Address("10.1.2.0"), ns.network.Ipv4Mask("255.255.255.0"))
csmaInterfaces = address.Assign(csmaDevices)

address.SetBase(ns.network.Ipv4Address("10.1.3.0"), ns.network.Ipv4Mask("255.255.255.0"))
if3if4 = address.Assign(d4d3)

#######################################################################################
# CREATE TCP APPLICATION AND CONNECTION
# 
# Re-used from the example sim-tcp.py

def SetupTcpConnection(srcNode, dstNode, dstAddr, startTime, stopTime):
  # Create a TCP sink at dstNode
  packet_sink_helper = ns.applications.PacketSinkHelper("ns3::TcpSocketFactory",
                          ns.network.InetSocketAddress(ns.network.Ipv4Address.GetAny(),
                                                       8080))
  sink_apps = packet_sink_helper.Install(dstNode)
  sink_apps.Start(ns.core.Seconds(2.0))
  sink_apps.Stop(ns.core.Seconds(50.0))

  # Create TCP connection from srcNode to dstNode
  on_off_tcp_helper = ns.applications.OnOffHelper("ns3::TcpSocketFactory",
                          ns.network.Address(ns.network.InetSocketAddress(dstAddr, 8080)))
  on_off_tcp_helper.SetAttribute("DataRate",
                      ns.network.DataRateValue(ns.network.DataRate(int(cmd.on_off_rate))))
  on_off_tcp_helper.SetAttribute("PacketSize", ns.core.UintegerValue(1500))
  on_off_tcp_helper.SetAttribute("OnTime",
                      ns.core.StringValue("ns3::ConstantRandomVariable[Constant=2]"))
  on_off_tcp_helper.SetAttribute("OffTime",
                        ns.core.StringValue("ns3::ConstantRandomVariable[Constant=1]"))
  #                      ns.core.StringValue("ns3::UniformRandomVariable[Min=1,Max=2]"))
  #                      ns.core.StringValue("ns3::ExponentialRandomVariable[Mean=2]"))

  # Install the client on node srcNode
  client_apps = on_off_tcp_helper.Install(srcNode)
  client_apps.Start(startTime)
  client_apps.Stop(stopTime)


SetupTcpConnection(n4n3.Get(0), csmaNodes.Get(0), csmaInterfaces.GetAddress(0),
                   ns.core.Seconds(2.0), ns.core.Seconds(40.0))


# Create Applications
# UDP server
udpServer = ns.applications.UdpServerHelper(91)

udpServerApps = udpServer.Install(udpServerNode)
udpServerApps.Start(ns.core.Seconds(1.0))
udpServerApps.Stop(ns.core.Seconds(30.0))

# UDP client
udpClient = ns.applications.UdpClientHelper(csmaInterfaces.GetAddress(1), 91)
udpClient.SetAttribute("MaxPackets", ns.core.UintegerValue(1000000))
udpClient.SetAttribute("Interval", ns.core.TimeValue(ns.core.Seconds (cmd.interval)))
udpClient.SetAttribute("PacketSize", ns.core.UintegerValue(1024))

udpClientApps = udpClient.Install(udpClientNode)
udpClientApps.Start(ns.core.Seconds(2.0))
udpClientApps.Stop(ns.core.Seconds(25.0))

# Background UDP application to flood the common bus
# taken from the task 1
# Create the server on port 70. Put it on node 2
echoServer = ns.applications.UdpEchoServerHelper(70)
serverApps = echoServer.Install(csmaNodes.Get(1))
serverApps.Start(ns.core.Seconds(10.0))
serverApps.Stop(ns.core.Seconds(30.0))

# Create the client application and connect it to node 1 and port 9. Configure number
# of packets, packet sizes, inter-arrival interval.
echoClient = ns.applications.UdpEchoClientHelper(csmaInterfaces.GetAddress(1), 70)
echoClient.SetAttribute("MaxPackets", ns.core.UintegerValue(1000000))
echoClient.SetAttribute("Interval",
                        ns.core.TimeValue(ns.core.MicroSeconds(200)))
echoClient.SetAttribute("PacketSize", ns.core.UintegerValue(1024))

# Put the client on node 0 and start sending at time 2.0s.
clientApps = echoClient.Install(csmaNodes.Get(2))
clientApps.Start(ns.core.Seconds(12.0))
clientApps.Stop(ns.core.Seconds(28.0))

ns.internet.Ipv4GlobalRoutingHelper.PopulateRoutingTables()

# Dump packets
pointToPoint.EnablePcap("ring2", d0d1.Get(1), True)
csma.EnablePcap ("csma", csmaDevices.Get(0), True)
csma.EnablePcap ("csma", csmaDevices.Get(1), True)
csma.EnablePcap ("csma", csmaDevices.Get(2), True)

#######################################################################################
# FLOW MONITOR
#
# taken from the example code.

flowmon_helper = ns.flow_monitor.FlowMonitorHelper()
monitor = flowmon_helper.InstallAll()

ns.core.Simulator.Stop(ns.core.Seconds(50.0))
ns.core.Simulator.Run()

#######################################################################################
# FLOW MONITOR ANALYSIS
#
# taken from the example

monitor.CheckForLostPackets()

classifier = flowmon_helper.GetClassifier()

for flow_id, flow_stats in monitor.GetFlowStats():
  t = classifier.FindFlow(flow_id)
  proto = {6: 'TCP', 17: 'UDP'} [t.protocol]
  print ("FlowID: %i (%s %s/%s --> %s/%i)" %
          (flow_id, proto, t.sourceAddress, t.sourcePort, t.destinationAddress, t.destinationPort))

  print ("  Tx Bytes: %i" % flow_stats.txBytes)
  print ("  Rx Bytes: %i" % flow_stats.rxBytes)
  print ("  Lost Pkt: %i" % flow_stats.lostPackets)
  print ("  Flow active: %fs - %fs" % (flow_stats.timeFirstTxPacket.GetSeconds(),
                                       flow_stats.timeLastRxPacket.GetSeconds()))
  print ("  Throughput: %f Mbps" % (flow_stats.rxBytes *
                                     8.0 /
                                     (flow_stats.timeLastRxPacket.GetSeconds()
                                       - flow_stats.timeFirstTxPacket.GetSeconds())/
                                     1024/
                                     1024))


ns.core.Simulator.Destroy()