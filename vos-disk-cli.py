#!/usr/bin/env python3
import argparse
import subprocess

def check_disk_exists(disk):
    # Check that the disk exists
    output = subprocess.check_output(["lsblk","-dno","name"]).decode().strip()
    disks = output.splitlines()
    if disk not in disks:
        print(f"Eroor: device /dev/{disk} Not found")
        exit(1)

def get_disk_info(disk):
    check_disk_exists(disk)
    # get disk smart info
    disk_info = subprocess.check_output(["smartctl","-i",f"/dev/{disk}"]).decode()
    lines = disk_info.split("\n")
    Serial_Number = ""
    Device_Model = ""
    for line in lines:
        if line.startswith("Serial Number:"):
            Serial_Number = line.split(":")[1].strip()
        elif line.startswith("Device Model:"):
            Device_Model = line.split(":")[1].strip()

    return Serial_Number,Device_Model

def show_disk_info(disk):
    Serial_Number,Device_Model = get_disk_info(disk)
    if Serial_Number and Device_Model:
        print(f"Disk /dev/{disk} info:")
        print(f"Serial Number:   {Serial_Number}")
        print(f"Device Model:    {Device_Model}")
    else:
        print(f"Disk /dev/{disk}: Unable to detect device type")

def disk_light_on(disk, light_on_by="dd"):
    print("disk light on")
    get_disk_info(disk)
    if light_on_by == "dd":
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