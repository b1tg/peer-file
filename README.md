


B listen on tcp and ready to recv file
A connect to B and send file to B

on B: 

        python peer.py listen

on A:

        python peer.py client <file-path>
