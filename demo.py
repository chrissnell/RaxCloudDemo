#!/usr/bin/python

from prettytable import PrettyTable

import time
import re
import os
from sys import exit

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud.loadbalancer.base import Member, Algorithm
from libcloud.loadbalancer.types import State
from libcloud.loadbalancer.types import Provider as lb_Provider
from libcloud.loadbalancer.providers import get_driver as lb_get_driver
import libcloud.security

# Check to see if CA_CERT_PATH is set in the user's enviornment
if 'CA_CERT_PATH' in os.environ.keys():
    print "CA_CERT_PATH found."
    libcloud.security.CA_CERTS_PATH.append((os.environ)['CA_CERT_PATH'])

#
# Configuration
#
RACKSPACE_USER=os.environ['OS_USERNAME']
RACKSPACE_KEY=os.environ['OS_PASSWORD']
RACKSPACE_AUTH_URL=os.environ['OS_AUTH_URL']
TARGET_DC='dfw'
REGION='us'
AUTH_VERSION = '2.0'

active_servers = []

def is_number(s):
   try:
      float(s)
      return True
   except ValueError:
      return False

def create_server():

   global active_servers

   print "\nStandby. Connecting to Rackspace Cloud API endpoint...\n"

   Driver = get_driver(Provider.RACKSPACE)
   driver_kwargs = {'datacenter' : TARGET_DC}
   conn = Driver(RACKSPACE_USER, RACKSPACE_KEY, ex_force_auth_version=AUTH_VERSION, **driver_kwargs)

   images = conn.list_images()
   sizes = conn.list_sizes()
   locations = conn.list_locations()

   server_count = raw_input("How many servers do you wish to create? (1-20) [1] ") or 1

   print "Will create " + str(server_count) + " servers.\n\n"


   def sortfn(s):
      return s.name

   images = sorted(images, key=sortfn)

   table = PrettyTable(["#","Image"])
   table.align = "l"

   i = 0
   for x in images:
      table.add_row([i,x.name])
      i += 1

   print table

   # Find the Ubuntu image
   im = [i for i, item in enumerate(images) if re.search('12\.04', str(item))][0]

   user_input = raw_input("Please select an image. [%s] "  % im) or im

   im = images[int(user_input)]

   print "\nImage selected: " + images[int(user_input)].name
   print "\n"


   def sortfn_size(s):
       return s.ram

   sizes =  sorted(sizes, key=sortfn_size)

   table = PrettyTable(["#","Size (MB)","Price: $/hr"])
   table.align = "l"

   i = 0
   for x in sizes:
      table.add_row([i,x.ram,x.price])
      i += 1

   print table
   
   # Find the 2GB size
   sz = [i for i, item in enumerate(sizes) if re.search('2048', str(item))][0]

   user_input = raw_input("Please select a server size. [%s] " % sz) or sz

   sz = sizes[int(user_input)]

   print "\nSize selected: " + str(sizes[int(user_input)].ram) + " MB \n"

   print "Choose a hostname for this server."
   print "Note: for server quantities > 1, your server hostname will be appended with a serial number.\n"

   hostname = raw_input("Server hostname: ")

   while True:
       if len(hostname) == 0:
           hostname = raw_input("Please choose a server hostname: ")
       else:
           break

   if (server_count > 1):
      for i in range(int(server_count)):
          serial = "%03d" % (int(i) + 1)
          hname = hostname + "-" + str(serial)
          print "Creating [" + hname + "] ..."
          newnode = conn.create_node(name=hname,size=sz,image=im,location=locations[0])
          active_servers.append(newnode)
   else:
      print "Creating [" + hostname + "] ..."
      newnode = conn.create_node(name=hostname,size=sz,image=im,location=locations[0])
      active_servers.append(newnode)      


def delete_server():

   server_list = list_servers()

   print ""
   server_to_del = raw_input("Which server do you wish to delete? ('X' to cancel) [X] ") or "X"

   if (is_number(server_to_del)):

      if len(server_list) < int(server_to_del):
          print "\nInvalid server.\n"
          delete_server()
          return

      hostname_to_del = str(server_list[int(server_to_del) - 1].name) 

      print ""
      confirm = raw_input("Are you *sure* that you want to delete " + hostname_to_del + " ? [y/N] ").upper() or "N"

      print ""
      if (confirm == 'Y'):
         print "Deleting " + hostname_to_del + "..."

         Driver = get_driver(Provider.RACKSPACE)
         driver_kwargs = {'datacenter' : TARGET_DC}
         conn = Driver(RACKSPACE_USER, RACKSPACE_KEY, **driver_kwargs)

         if (conn.destroy_node(server_list[int(server_to_del) - 1])):
             print "Server deletion successful."
         else:
             print "Server deletion failed."
         
      else:
         print "Deletion cancelled."



def list_servers():
   print "\nStandby. Connecting to Rackspace Cloud API endpoint...\n"

   Driver = get_driver(Provider.RACKSPACE)
   driver_kwargs = {'datacenter' : TARGET_DC}
   conn = Driver(RACKSPACE_USER, RACKSPACE_KEY, **driver_kwargs)

   nodes = conn.list_nodes()

   table = PrettyTable(["#","name","public_ip","id"])
   table.align = "l"

   i = 1
   for x in nodes:
       if (len(x.public_ip) != 0):
           ips = x.public_ip
           ips.sort(lambda x,y: cmp(len(x), len(y)))
       else:
           ips = [ "not_yet_assigned" ]

       table.add_row([i,x.name,ips[0],x.id])
       i += 1

   print table

   return nodes

def create_lb():
   print "Creating a LB..."

   print "\nStandby. Connecting to Rackspace Cloud API endpoint...\n"

   Driver = get_driver(Provider.RACKSPACE_US)
   driver_kwargs = {'datacenter' : TARGET_DC}
   conn = Driver(RACKSPACE_USER, RACKSPACE_KEY, **driver_kwargs)

   protocols = conn.list_protocols()

   for p in protocols:
      print "Protocol: " + p


def add_lb_node():
   print "Adding node to LB..."

def remove_lb_node():
   print "Removing a node from an LB..."

def quit_and_cleanup():
   print "Quitting and cleaning up..."
   exit(0)


def main_menu():
   print "\n"
   print "Main Menu"
   print "-------------------------------------"
   print "(C) Create a server"
   print "(D) Delete a server"
   print "(L) List servers"
   print "(B) Create a load balancer"
   print "(A) Add nodes to load balancer"
   print "(R) Remove nodes from load balancer"
   print "(X) Exit\n"
   user_input = raw_input("--> ").upper()

   if len(user_input) == 0:
      return

   user_input = re.sub('\s+', '', user_input)[0]

   actions_main = {'C' : create_server,
                   'D' : delete_server,
                   'L' : list_servers,
                   'B' : create_lb,
                   'A' : add_lb_node,
                   'R' : remove_lb_node,
                   'X' : quit_and_cleanup }

  
   if (len(user_input) == 0):
       main_menu()
   else: 
       if user_input in actions_main:
          action_func = actions_main[user_input] 
          action_func()
       else:
          print "\nInvalid command: " + user_input
          return

#   main_menu()


while True:
    main_menu()
