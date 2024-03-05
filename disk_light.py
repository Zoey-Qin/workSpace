#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os

def check_root():
    if os.geteuid() != 0:
        print("This script requires root privileges. Please run it as root.")
        sys.exit(1)

def check_disk_exists(disk):
    # Check that the disk exists
    output = subprocess.check_output(["lsblk","-dno","name"]).decode().strip()
    disks = output.splitlines()
    if disk not in disks:
        print(f"Error: device /dev/{disk} Not found")
        exit(1)

def get_disk_info(disk):
    check_disk_exists(disk)
    # get disk smart info
    disk_info = subprocess.check_output(["smartctl", "-i", f"/dev/{disk}"]).decode()
    lines = disk_info.split("\n")
    serial_number = ""
    device_model = ""
    disk_is_light = False

    # get disk Serial_number and Device_model
    for line in lines:
        if line.startswith("Serial Number:"):
            serial_number = line.split(":")[1].strip()
        elif line.startswith("Device Model:"):
            device_model = line.split(":")[1].strip()

    # check if disk_light_on is running
    service_name = f"{disk}_light_on.service"
    try:
        disk_light_status = subprocess.check_output(["systemctl", "is-active", service_name])
        if disk_light_status.strip().decode() == "active":
            disk_is_light = True
            print(f"debug: {disk} led light is on")
    except subprocess.CalledProcessError:
        disk_is_light = False
        print(f"debug: {disk} led light is off")

    return serial_number,device_model,disk_is_light

def show_disk_info(disk):
    Serial_Number,Device_Model,disk_is_light = get_disk_info(disk)
    if Serial_Number and Device_Model:
        print(f"Disk /dev/{disk} info:")
        print(f"Serial Number:   {Serial_Number}")
        print(f"Device Model:    {Device_Model}")
        if disk_is_light:
            print(f"/dev/{disk} LED is TurnOn")
        else:
            print(f"/dev/{disk} LED is TurnOff")
    else:
        print(f"Disk /dev/{disk}: Unable to detect device type,it may be of type NVMe, or it may not be a physical disk.")

def light_on_by_dd(disk):
    service_name = f"{disk}_light_on.service"
    service_content = f"""\
[Unit]
Description=Disk Light On Service for /dev/{disk}

[Service]
Type=simple
ExecStart=/usr/bin/dd if=/dev/{disk} of=/dev/null bs=1M

[Install]
WantedBy=multi-user.target
"""
    # create service file
    service_file_path = f"/etc/systemd/system/{service_name}"
    with open(service_file_path, "w") as f:
        f.write(service_content)
    # start service
    subprocess.run(["systemctl", "enable", service_name])
    subprocess.run(["systemctl", "start", service_name])
    # check service status
    disk_light_status =get_disk_info(disk)[2]

def disk_light_on(disk, light_on_by="dd"):
    print("disk light on")
    disk_is_light = get_disk_info(disk)[2]
    if disk_is_light:
        print(f"The led of {disk} has already been turned on, there is no need to turn it on repeatedly.")
        exit(0)
    if light_on_by == "dd":
        light_on_by_dd(disk)
    if light_on_by == "megacli":
        pass
    if light_on_by == "libstorage":
        pass

def disk_light_off(disk):
    get_disk_info(disk)
    print("disk light off")



def main():
    # create a parser and add parameters
    parser = argparse.ArgumentParser(description="Manage disk options")
    parser.add_argument("--show",
        type=str,
        metavar="[disk]",
        help="Displays important information about the specified disk",
    )
    parser.add_argument("--lightOn",
        type=str,
        metavar="[disk]",
        help="Turn on the light of the specified disk",
    )
    parser.add_argument("--lightOnBy",
        type=str,
        metavar="[tool]",
        choices=['dd','megacli','libstorage'],
        help="Turn on the light of the specified disk by which tools",
    )
    parser.add_argument("--lightOff",
        metavar="[disk]",
        help="Turn off the light of thespecified disk",
    )

    # Parsing command line arguments
    args = parser.parse_args()

    if args.show:
        show_disk_info(args.show)

    if args.lightOnBy:
        if not args.lightOn:
            parser.error("--lightOnBy must be used with --lightOn")

    if args.lightOn:
        if args.lightOnBy:
            disk = args.lightOn
            tool = args.lightOnBy
            disk_light_on(disk,tool)
        else:
            disk = args.lightOn
            disk_light_on(disk)

            if args.lightOff:
        disk_light_off(args.lightOff, "dd")

if __name__ == '__main__':
    main()
