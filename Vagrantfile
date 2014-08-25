# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"


Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.provider "virtualbox" do |v|
    v.gui = true
  end

  config.vm.provider "virtualbox" do |vb|
    vb.customize ["modifyvm", :id, "--memory", "1024", "--vram", "256"]
  end

  config.vm.box = "Microsoft Windows 7 Enterprise Edition (32-bit)"
  config.vm.box_url = "http://vagrantboxes.devopslive.org/windows-7-enterprise-i386.box"

  config.vm.synced_folder ".", "/vagrant", type: "smb"

  # config.vm.network "public_network", :bridged => 'eth0' #, :mac => "0800DEADBEEF"

  # NOTE: this has to be here as a relogin is required between the base setup and the rest
  # this is to clean cgroups from "apt-get remove -y --purge libpam-systemd"
  #config.vm.provision "shell", path: "scripts/host/lxc-base.sh"

  # and we have to SSH to ourselves to get a new session free of the old cgroup
  #config.vm.provision "shell", inline: "ssh -oStrictHostKeyChecking=no localhost /vagrant/scripts/app/setup-everything.sh"

end
