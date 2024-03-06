#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os

def check_root():
    """
    Checks whether the user is root.
    """
    if os.geteuid() != 0:
        print("This script requires root privileges. Please run it as root.")
        sys.exit(1)

def check_disk_exists(disk):
    """
    Checks whether the specified disk exists.
    parameter:
        - disk: The string, the specified disk device name, such as 'sda'.
    """
    # Check that the disk exists
    output = subprocess.check_output(["lsblk","-dno","name"]).decode().strip()
    disks = output.splitlines()
    if disk not in disks:
        print(f"Error: device /dev/{disk} Not found")
        sys.exit(1)

def get_disk_info(disk):
    """
    Gets the information about the specified disk, including the serial number, \
        whether it is of the NVMe type, and whether the disk_light_on service is active.
    parameter:
        - disk: The string, the specified disk device name, such as 'sda'.
    returned value:
        - serial_number: String, the serial number of the disk.
        - disk_is_light: Boolean indicating whether the disk_light_on service is running.
        - disk_is_nvme: Boolean indicating whether the disk is of NVMe type.
    """
    check_disk_exists(disk)
    # check if disk is NVMe type
    nvme_list = subprocess.check_output(["nvme", "list"]).decode()
    disk_is_nvme = f"/dev/{disk}" in nvme_list
    # get disk smart info
    disk_info = subprocess.check_output(["smartctl", "-i", f"/dev/{disk}"]).decode()
    lines = disk_info.split("\n")
    serial_number = ""
    disk_is_light = False
    # get disk Serial_number
    for line in lines:
        if line.startswith("Serial Number:"):
            serial_number = line.split(":")[1].strip()
    # check if disk_light_on is running
    if not disk_is_nvme:
        service_name = f"{disk}_light_on.service"
        try:
            disk_light_status = subprocess.check_output(["systemctl", "is-active", service_name])
            if disk_light_status.strip().decode() == "active":
                disk_is_light = True
        except subprocess.CalledProcessError:
            disk_is_light = False

    return serial_number,disk_is_light,disk_is_nvme

def show_disk_info(disk):
    """
    Shows the information about the specified disk, including the serial number, \
        whether it is of the NVMe type, and whether the disk_light_on service is active.
    parameter:
        - disk: The string, the specified disk device name, such as 'sda'.
    """
    serial_number,disk_is_light,disk_is_nvme = get_disk_info(disk)
    if serial_number:
        print(f"Disk /dev/{disk} info:")
        print(f"Serial Number:   {serial_number}")
        if disk_is_nvme:
            print(f"Disk /dev/{disk} is NVMe type")
            sys.exit (0)
        if disk_is_light:
            print(f"/dev/{disk} LED is TurnOn")
            sys.exit (0)
        else:
            print(f"/dev/{disk} LED is TurnOff")
            sys.exit (0)
    else:
        print(f"Disk /dev/{disk}: Unable to detect device type,it may not be a physical disk.")

def light_on_by_dd(disk):
    """
    Turns on the LED light of the specified disk.
    parameter:
        - disk: The string, the specified disk device name, such as 'sda'.
    """
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
    with open(service_file_path, "w",encoding="utf-8") as f:
        f.write(service_content)
    # start service
    subprocess.run(["systemctl", "start", service_name],check=True)
    # check service status
    disk_is_light =get_disk_info(disk)[1]
    if disk_is_light:
        print(f"Disk {disk} is light up successfully.")
        sys.exit (0)
    else:
        print(f"Disk {disk} is light up failed, please check it.")
        sys.exit(1)

def disk_light_on(disk, light_on_by="dd"):
    """
    Turns on the LED light of the specified disk.
    parameter:
        - disk: The string, the specified disk device name, such as 'sda'.
        - light_on_by: The string, the method to turn on the LED light, \
            dd: dd command, megacli: megacli command, libstorage: libstorage command.
    """
    _,disk_is_light,disk_is_nvme = get_disk_info(disk)
    if disk_is_nvme:
        print(f"Disk {disk} is NVMe type, it does not support LED light.")
        sys.exit(1)
    if disk_is_light:
        print(f"The led of {disk} has already been turned on,\
there is no need to turn it on repeatedly.")
        sys.exit(0)
    if light_on_by == "dd":
        light_on_by_dd(disk)
    if light_on_by == "megacli":
        pass
    if light_on_by == "libstorage":
        pass

def disk_light_off(disk):
    """
    Turns off the LED light of the specified disk.
    parameter:
        - disk: The string, the specified disk device name, such as 'sda'.
    """
    # check service status
    disk_is_light =get_disk_info(disk)[1]
    if disk_is_light:
        service_name = f"{disk}_light_on.service"
        subprocess.run(["systemctl", "stop", service_name],check=True)
        subprocess.run(["systemctl", "disable", service_name],check=True)
        # check service status
        disk_is_light =get_disk_info(disk)[1]
        if not disk_is_light:
            print(f"Disk {disk} LED turn off successfully.")
            service_file = f"/etc/systemd/system/{disk}_light_on.service"
            try:
                subprocess.run(["rm",service_file],check=True)
                sys.exit (0)
            except FileNotFoundError:
                print(f"Disk {disk} light serive not found,may be the disk is not light.")
                sys.exit (1)
    else:
        print(f"Disk {disk} LED is not light.")
        sys.exit (0)

def main():
    """
    Main function
    """
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
    args , unknown = parser.parse_known_args()
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
        disk_light_off(args.lightOff)
    # Check if no arguments are provided
    if not any(vars(args).values()):
        print("No arguments provided, please use --help to see the usage.")
if __name__ == '__main__':
    main()
