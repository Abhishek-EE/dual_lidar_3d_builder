#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 16 13:57:01 2023

@author: acms2
"""

import pyudev

def find_usb_tty_devices():
    context = pyudev.Context()
    usb_tty_devices = []
    
    for device in context.list_devices(subsystem="tty"):
        #check if device is usb tty device
        if 'ID_VENDOR_ID' in device.properties:
            print(device.properties)

            
            usb_tty_devices.append(device.device_node)
            
    return usb_tty_devices

            
usb_devices = find_usb_tty_devices()

if usb_devices:
    print("USB TTY DEVICES")
    print("========")
    for dev in usb_devices:
        vendor_id = dev.properties['ID_VENDOR_ID']
        model_id = dev.properties['ID_MODEL_ID']
        print(dev.device_type)
        print(dev.device_node)
        print("===")
else:
    print("NO TTY DEVICES")
