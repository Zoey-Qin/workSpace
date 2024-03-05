#!/usr/bin/env python3
import argparse
import subprocess
import sys
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
    Serial_Number = ""
    Device_Model = ""
    disk_is_light = False

    # get disk Serial_number and Device_model
    for line in lines:
        if line.startswith("Serial Number:"):
            Serial_Number = line.split(":")[1].strip()
        elif line.startswith("Device Model:"):
            Device_Model = line.split(":")[1].strip()

    return Serial_Number, Device_Model, disk_is_light

def show_disk_info(disk):
    Serial_Number,Device_Model,__= get_disk_info(disk)
    if Serial_Number and Device_Model:
        print(f"Disk /dev/{disk} info:")
        print(f"Serial Number:   {Serial_Number}")
        print(f"Device Model:    {Device_Model}")
    else:
        print(f"Disk /dev/{disk}: Unable to detect device type,it may be of type NVMe, or it may not be a physical disk.")

def light_on_by_dd(disk):
    print(f"debug:{disk} led start lit on")
    print(f"debug:{disk} led is lit")
    print(f"Enter Ctrl-C to Turn off {disk} led")
    subprocess.run(["dd","if=/dev/{disk}","of=/dev/null","bs=1M"])


def disk_light_on(disk, light_on_by="dd"):
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
        choices=['dd'],
        help="Turn on the light of the specified disk by which tools",
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
            disk_light_on(args.lightOn,args.lightOnBy)
        else:
            disk_light_on(args.lightOn)


if __name__ == '__main__':
    main()
