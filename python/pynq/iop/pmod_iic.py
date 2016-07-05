#   Copyright (c) 2016, Xilinx, Inc.
#   All rights reserved.
# 
#   Redistribution and use in source and binary forms, with or without 
#   modification, are permitted provided that the following conditions are met:
#
#   1.  Redistributions of source code must retain the above copyright notice, 
#       this list of conditions and the following disclaimer.
#
#   2.  Redistributions in binary form must reproduce the above copyright 
#       notice, this list of conditions and the following disclaimer in the 
#       documentation and/or other materials provided with the distribution.
#
#   3.  Neither the name of the copyright holder nor the names of its 
#       contributors may be used to endorse or promote products derived from 
#       this software without specific prior written permission.
#
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, 
#   THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR 
#   PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, 
#   EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, 
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
#   OR BUSINESS INTERRUPTION). HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
#   WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR 
#   OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF 
#   ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

__author__      = "Yun Rock Qu"
__copyright__   = "Copyright 2016, Xilinx"
__email__       = "pynq_support@xilinx.com"

from time import sleep
from pynq.iop import pmod_const
from pynq.iop.devmode import DevMode

I2C_DELAY = .001

class PMOD_IIC(object):
    """This class controls the PMOD IIC pins.
    
    Note
    ----
    The index of the PMOD pins:
    upper row, from left to right: {vdd,gnd,3,2,1,0}.
    lower row, from left to right: {vdd,gnd,7,6,5,4}.
    
    Attributes
    ----------
    iop : _IOP
        The _IOP object returned from the DevMode.
    scl_pin : int
        The SCL pin number.
    sda_pin : int
        The SDA pin number.
    iic_addr : int
        The IIC device address.
    sr_addr : int
        The IIC device SR address (base address + 0x104).
    dtr_addr : int
        The IIC device DTR address (base address + 0x108).
    cr_addr : int
        The IIC device CR address (base address + 0x100).
    rfd_addr : int
        The IIC device RFD address (base address + 0x120).
    drr_addr : int
        The IIC device DRR address (base address + 0x10C).
    
    """
    def __init__(self, pmod_id, scl_pin, sda_pin, iic_addr): 
        """Return a new instance of a PMODIIC object.
    
        Note
        ----
        The pmod_id 0 is reserved for XADC (JA).
        
        Parameters
        ----------
        pmod_id : int
            The PMOD ID (1, 2, 3, 4) corresponding to (JB, JC, JD, JE).
        scl_pin : int
            The SCL pin number.
        sda_pin : int
            The SDA pin number.
        iic_addr : int
            The IIC device address.
            
        """
        if (scl_pin not in range(8)):
            raise ValueError("Valid SCL pin numbers are 0 - 7.")
        if (sda_pin not in range(8)):
            raise ValueError("Valid SDA pin numbers are 0 - 7.")
        
        switchconfig = []
        for i in range(8):
            if i == sda_pin:
                switchconfig.append(pmod_const.IOP_SWCFG_IIC0_SDA)
            elif i == scl_pin:
                switchconfig.append(pmod_const.IOP_SWCFG_IIC0_SCL)
            else:
                switchconfig.append(pmod_const.IOP_SWCFG_PMODIO0)
        
        self.iop = DevMode(pmod_id, switchconfig)
        self.iop.start()
        self.iop.load_switch_config()
        
        self.iic_addr = iic_addr

        # Useful IIC controller addresses
        self.sr_addr = pmod_const.IOPMM_XIIC_0_BASEADDR + \
                       pmod_const.IOPMM_XIIC_SR_REG_OFFSET

        self.dtr_addr = pmod_const.IOPMM_XIIC_0_BASEADDR + \
                        pmod_const.IOPMM_XIIC_DTR_REG_OFFSET

        self.cr_addr = pmod_const.IOPMM_XIIC_0_BASEADDR + \
                       pmod_const.IOPMM_XIIC_CR_REG_OFFSET
    
        self.rfd_addr = pmod_const.IOPMM_XIIC_0_BASEADDR + \
                        pmod_const.IOPMM_XIIC_RFD_REG_OFFSET

        self.drr_addr = pmod_const.IOPMM_XIIC_0_BASEADDR + \
                        pmod_const.IOPMM_XIIC_DRR_REG_OFFSET

    def _iic_enable(self):
        """This method enables the IIC drivers.
        
        The correct sequence to enable the drivers is:
        1. Disale the IIC core.
        2. Set the Rx FIFO depth to maximum.
        3. Reset the IIC core and flush the Tx FIFO.
        4. Enable the IIC core.
        
        Note
        ----
        This function is only required during initialization.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        
        """
        # Disable the IIC core
        self.iop.write_cmd(self.cr_addr, 0x00)
        # Set the Rx FIFO depth to maximum
        self.iop.write_cmd(self.rfd_addr, 0x0F)       
        # Reset the IIC core and flush the Tx FIFO
        self.iop.write_cmd(self.cr_addr, 0x02)
        # Enable the IIC core
        self.iop.write_cmd(self.cr_addr, 0x01)
        
        sleep(I2C_DELAY)


    def send(self, iic_bytes):
        """This method sends the command or data to the driver.
        
        Parameters
        ----------
        iic_bytes : list
            A list of 8-bit bytes to be sent to the driver.
            
        Returns
        -------
        None
        
        Raises
        ------
        RuntimeError
            Timeout when waiting for the FIFO to be empty.
            
        """
        # Enable IIC Core
        self._iic_enable()
        
        # Transmit 7-bit address and Write bit (with START)
        self.iop.write_cmd(self.dtr_addr, 0x100 | (self.iic_addr << 1))
        
        # Iteratively write into Tx FIFO, wait for it to be empty        
        for tx_cnt in range(len(iic_bytes)):
            timeout = 100
            
            # Construct the TX word
            if (tx_cnt == len(iic_bytes) - 1):
                tx_word = (0x200 | iic_bytes[tx_cnt])
            else:
                tx_word = iic_bytes[tx_cnt]
            
            # Write data
            self.iop.write_cmd(self.dtr_addr, tx_word)
            while ((timeout > 0) and \
                        ((self.iop.read_cmd(self.sr_addr) & 0x80) == 0x00)):
                timeout -= 1
            if (timeout == 0):
                raise RuntimeError("Timeout when writing IIC.")

        sleep(I2C_DELAY)

    def receive(self, num_bytes):
        """This method receives IIC bytes from the device.
        
        Parameters
        ----------
        num_bytes : int
            Number of bytes to be received from the device.
            
        Returns
        -------
        iic_bytes : list
            A list of 8-bit bytes received from the driver.
        
        Raises
        ------
        RuntimeError
            Timeout when waiting for the RX FIFO to fill.
            
        """

        # Reset the IIC core and flush the Tx FIFO
        self.iop.write_cmd(self.cr_addr, 0x02)

        # Set the Rx FIFO depth to one byte
        self.iop.write_cmd(self.rfd_addr, 0x0) 

        # Transmit 7-bit address and Read bit
        self.iop.write_cmd(self.dtr_addr, 0x101 | (self.iic_addr << 1))

        # Enable the IIC core
        cr_reg = 0x05
        if num_bytes == 1:
            cr_reg |= 0x10

        self.iop.write_cmd(self.cr_addr,cr_reg)
        sleep(I2C_DELAY)

        # Program IIC Core to read num_bytes bytes and issue STOP
        self.iop.write_cmd(self.dtr_addr, 0x200 + num_bytes)

        # Read num_bytes from RX FIFO
        iic_bytes = list()
        while(len(iic_bytes) < num_bytes):
 
            # Special condition for last two bytes
            if (num_bytes - len(iic_bytes)) == 1:
                self.iop.write_cmd(self.cr_addr,0x1)
            elif (num_bytes - len(iic_bytes)) == 2:
                self.iop.write_cmd(self.cr_addr, \
                                   self.iop.read_cmd(self.cr_addr) | 0x10)

            # Wait for data to be available in RX FIFO
            timeout = 100
            while(((self.iop.read_cmd(self.sr_addr) & 0x40) == 0x40) and \
                  (timeout > 0)):
                timeout -= 1

            if(timeout == 0):
                raise RuntimeError("Timeout when reading IIC.")

            # Read data 
            iic_bytes.append((self.iop.read_cmd(self.drr_addr) & 0xff))

        sleep(I2C_DELAY)
        return iic_bytes
        
