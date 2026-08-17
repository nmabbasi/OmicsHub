---
title: "Connecting to HPC"
date: "2025-08-23"
author: "Nasir Mahmood Abbasi, PhD"
category: "High-Performance Computing (HPC)"
excerpt: "Set up secure SSH connections to remote HPC systems from Windows and macOS, configure MobaXterm for graphical access, and establish your working environment on the cluster."
image: "images/hpc-connecting-to-cluster.webp"
---


<div class="flex flex-wrap items-center gap-4 text-xs font-mono text-gray-500 bg-gray-50 p-3 rounded-lg border border-gray-200 mb-6">
  <div class="flex items-center gap-1">
    <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
    <span><strong>Tested on:</strong> Python 3.11, R 4.3.2, Ubuntu 24.04</span>
  </div>
  <div class="flex items-center gap-1">
    <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
    <span><strong>Last Review:</strong> 2026-08-15</span>
  </div>
</div>

<div class="p-6 bg-blue-50 border border-blue-100 rounded-xl mb-8">
  <h4 class="text-lg font-bold text-blue-900 mb-2">Learning Objectives & Prerequisites</h4>
  <ul class="list-disc list-inside text-blue-800 space-y-1 mb-4">
    <li><strong>Prerequisites:</strong> Complete Basic Navigation and obtain cluster hostname, username, authentication method, and local terminal access from your institution.</li>
    <li><strong>Objective:</strong> Connect securely to an HPC cluster with SSH, transfer files appropriately, and distinguish local from remote paths.</li>
    <li><strong>Expected Output:</strong> A documented SSH configuration and a successful login to the assigned cluster without exposing credentials.</li>
  </ul>
  <p class="text-sm text-blue-700"><strong>Suggested route:</strong> use the <a href="start-here.html" class="underline">Bioinformatics Learning Path</a> to review any prerequisite stage before continuing.</p>
</div>



## Connecting with SSH (Windows)

## Windows

Download and install [MobaXterm](https://mobaxterm.mobatek.net/download.html).

### Generating a pair of keys

Run MobaXterm, click on `Start local terminal`, and execute the following command:

```bash
ssh-keygen -t rsa -f my_hpc_key
```

This command will prompt you for a _passphrase_ twice and create two files: `my_hpc_key` (the private key) and `my_hpc_key.pub` (the public key). Keep both files in a protected local folder such as `C:\Users\XXX\Documents\MobaXterm\home\` (replace `XXX` with your user name).

### What to do with the keys

> **Security rule:** Keep `my_hpc_key` on your local computer. Never email it, upload it to cloud storage, commit it to Git, or copy it to the cluster or another remote host. The cluster administrator authorizes the matching **public** key (`my_hpc_key.pub`) in your account, usually in `~/.ssh/authorized_keys`.

When connecting from another trusted personal computer, create a separate local key pair for that device and ask the administrator to add that device's public key. Use the private key only in the SSH client running on the computer you control.

### Connecting with SSH

If you want to run graphical applications from outside the university’s network, or if you prefer a graphical desktop, refer to the [Connecting with NX](#connecting-with-nx) section.

####  From inside the university’s network

In the MobaXterm window:

*   Click on `Session` (upper left corner), then `SSH`.
*   Fill the `Remote Host` field with `hpc.example.edu` (replace with your institution's HPC address).
*   Tick the `Specify username` box and enter the login name provided by the administrator.
*   In the `Advanced SSH settings` tab, tick the `Use private key` box and set its location to your private key file.
*   Click `OK`.
*   A new session should appear in the left panel; double-click it to connect.

![ssh](images/ssh.png)

####  From outside the university’s network

Once connected via VPN, refer to the instructions in the "From inside the university’s network" section above to establish your SSH connection.

###  File transfer

Once connected with MobaXterm, you can easily transfer files by dragging and dropping them in the left panel.

## Connecting with SSH (Linux / Mac)

## Connecting with SSH

If you want to run graphical applications from outside the university’s network, or if you prefer a graphical desktop over the console, refer to the [Connecting with NX](#connecting-with-nx) section.

### From inside the university’s network

Add the following lines to your `~/.ssh/config` file. Replace `your_username` with the login name provided by the administrator:

```
Host hpc_alias
        Hostname hpc.example.edu
        User your_username
        IdentityFile ~/.ssh/my_hpc_key
```

**Explanation:**
*   `Host hpc_alias`: This line defines an alias (`hpc_alias`). The options that follow this line will only be applied when `ssh` recognizes this alias.
*   `Hostname hpc.example.edu`: Specifies the address of the remote host.
*   `User your_username`: Defines the username to use for the connection.
*   `IdentityFile ~/.ssh/my_hpc_key`: Tells `ssh` to use the specified private key for authentication.

With this configuration, you can connect using:

```bash
ssh hpc_alias
```

**Important**: The following command will **not** work as expected because the `IdentityFile` option will not be used:

```bash
ssh your_username@hpc.example.edu
```

The alias `hpc_alias` can be changed to any name you prefer.

### From outside the university’s network

To connect from outside the university’s network, you must first request VPN access from the network administrator. Once granted, follow the instructions provided by the administrator.

Alternatively, if you prefer not to use a graphical VPN client (like `gnome` or `network-manager`), you can:

*   Install `openvpn`.
*   Download the configuration files from the provided address.
*   Extract the archive and navigate into the directory.
*   With root privileges, run:

    ```bash
    openvpn vpn-univ-TCP-443.ovpn
    ```

Once connected via VPN, refer to the instructions in the "From inside the university’s network" section above to establish your SSH connection.

## Connecting with NX

## Connecting with NX

Install [x2goclient](https://wiki.x2go.org/doku.php/doc:installation:x2goclient). It may be available as a package for your Linux/Mac distribution, or you can download it (also for Windows) from the provided link.

To set up a new session:

*   Click on `Session`, then `New session…`.
*   Optionally, change the `Session name`.
*   Enter `hpc.example.edu` in the `Host` field.
*   Fill in the `Login` field with your username.
*   Set the location of your private key in the `Use RSA/DSA key for ssh connection` field.
*   In the `Session type` box, choose either:
    *   `XFCE` for a graphical desktop environment.
    *   `Single application`, then `Terminal` from the right drop-down menu for a terminal session.
*   Click `Ok`. The session should appear in the right panel. Click on it to connect.

![X2GO](images/Nx.png)

**Important**: If you are outside the university’s network, you must first connect to the VPN. Refer to the [From outside the university’s network](#from-outside-the-universitys-network) section above for VPN instructions.




<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-4">Knowledge Check & Assessment</h3>
  <div class="space-y-4">
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">1. Concept Verification</h4>
      <p class="text-gray-600 text-sm">What information is needed to establish an SSH connection, and why should passwords or private keys never be shared?</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">2. Practical Execution</h4>
      <p class="text-gray-600 text-sm">Create an SSH config alias for an authorized cluster, log in, run hostname and pwd, then log out safely. <strong>Pass Criteria:</strong> Record the command or analysis choice, keep the output, and explain why it answers the stated task.</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">3. Troubleshooting</h4>
      <p class="text-gray-600 text-sm">If SSH fails, how will you distinguish an incorrect hostname, network/VPN issue, permissions problem, and authentication failure?</p>
    </div>
  </div>
</div>
