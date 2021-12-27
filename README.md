# pyKamstrup
Kamstrup Multical 602 reader script for pi

I use this reader: https://shop.weidmann-elektronik.de/index.php?page=product&info=24 but cheaper alternatives exist at AliExpress. Runs on my PiZero with a micro-usb to mini-usb otg cable.

Udev rules:

* lsusb
* sudo -s
* echo 'SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6015", SYMLINK="ttyKamstrup"' >> /etc/udev/rules.d/99-serialmeuk.rules
* udevadm trigger
