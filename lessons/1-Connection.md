---
title: "Connecting to an HPC Cluster: SSH, MobaXterm, and Remote Access"
date: "2025-08-23"
author: "OmicsHub Team"
category: "High-Performance Computing"
excerpt: "Set up secure SSH connections to remote HPC systems from Windows and macOS, configure MobaXterm for graphical access, and establish your working environment on the cluster."
image: "images/connection.png"
---

# Connecting with SSH (Windows)

## Windows

Download and install [MobaXterm](https://mobaxterm.mobatek.net/download.html).

### Generating a pair of keys

Run MobaXterm, click on `Start local terminal`, and execute the following command:

```bash
ssh-keygen -t rsa -f esmeralda
```

This command will prompt you for a _passphrase_ twice and create two files: `esmeralda` (the private key) and `esmeralda.pub` (the public key). These two files must be located in the `C:\Users\XXX\Documents\MobaXterm\home\` folder (replace `XXX` with your user name).

### What to do with the keys

Note that every host you use to connect to the cluster will require this private key.

### Connecting with SSH

If you want to run graphical applications from outside the university’s network, or if you prefer a graphical desktop, refer to the [Connecting with NX](#connecting-with-nx) section.

####  From inside the university’s network

In the MobaXterm window:

*   Click on `Session` (upper left corner), then `SSH`.
*   Fill the `Remote Host` field with `10.195.17.215`.
*   Tick the `Specify username` box and enter the login name provided by the administrator.
*   In the `Advanced SSH settings` tab, tick the `Use private key` box and set its location to your private key file.
*   Click `OK`.
*   A new session should appear in the left panel; double-click it to connect.

![ssh](images/ssh.png)

####  From outside the university’s network

Once connected via VPN, refer to the instructions in the "From inside the university’s network" section above to establish your SSH connection.

###  File transfer

Once connected with MobaXterm, you can easily transfer files by dragging and dropping them in the left panel.

# Connecting with SSH (Linux / Mac)

## Connecting with SSH

If you want to run graphical applications from outside the university’s network, or if you prefer a graphical desktop over the console, refer to the [Connecting with NX](#connecting-with-nx) section.

### From inside the university’s network

Add the following lines to your `~/.ssh/config` file. Replace `LOGIN` with the login name provided by the administrator:

```
Host esmeralda
        Hostname 10.195.17.215
        User LOGIN
        IdentityFile ~/.ssh/esmeralda
```

**Explanation:**
*   `Host esmeralda`: This line defines an alias (`esmeralda`). The options that follow this line will only be applied when `ssh` recognizes this alias.
*   `Hostname 10.195.17.215`: Specifies the IP address of the remote host.
*   `User LOGIN`: Defines the username to use for the connection.
*   `IdentityFile ~/.ssh/esmeralda`: Tells `ssh` to use the specified private key for authentication.

With this configuration, you can connect using:

```bash
ssh esmeralda
```

**Important**: The following command will **not** work as expected because the `IdentityFile` option will not be used:

```bash
ssh LOGIN@10.195.17.215
```

The alias `esmeralda` can be changed to any name you prefer.

### From outside the university’s network

To connect from outside the university’s network, you must first request VPN access from `administrator`. Once granted, follow the instructions provided by the administrator.

Alternatively, if you prefer not to use a graphical VPN client (like `gnome` or `network-manager`), you can:

*   Install `openvpn`.
*   Download the configuration files from the provided address.
*   Extract the archive and navigate into the directory.
*   With root privileges, run:

    ```bash
    openvpn vpn-univ-TCP-443.ovpn
    ```

Once connected via VPN, refer to the instructions in the "From inside the university’s network" section above to establish your SSH connection.

# Connecting with NX

## Connecting with NX

Install [x2goclient](https://wiki.x2go.org/doku.php/doc:installation:x2goclient). It may be available as a package for your Linux/Mac distribution, or you can download it (also for Windows) from the provided link.

To set up a new session:

*   Click on `Session`, then `New session…`.
*   Optionally, change the `Session name`.
*   Enter `10.195.17.215` in the `Host` field.
*   Fill in the `Login` field with your username.
*   Set the location of your private key in the `Use RSA/DSA key for ssh connection` field.
*   In the `Session type` box, choose either:
    *   `XFCE` for a graphical desktop environment.
    *   `Single application`, then `Terminal` from the right drop-down menu for a terminal session.
*   Click `Ok`. The session should appear in the right panel. Click on it to connect.

![X2GO](images/Nx.png)

**Important**: If you are outside the university’s network, you must first connect to the VPN. Refer to the [Linux/Mac SSH connection tutorial](hpc_connect_ssh_linux_mac.md) or [Windows SSH connection tutorial](hpc_connect_ssh_windows.md) for VPN instructions.


