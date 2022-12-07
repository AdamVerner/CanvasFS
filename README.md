  After droping one class i realized i dont need this project anymore, so i gave up :)
  It still should somehow work as is, but no further effort will be put into the project.
  
# InstructureFS

## Usage

### Linux
Simply run the `main.py` with specified mountpoint and access token.

```shell
pytohn3 main.py MOUNTPOINT [file containing access token]
```


### Windows
The project cannot be directly used on Windows yet as it heavily relies on FUSE.
WSL2 can be used to mount the directory, which can later be accessed by Windows explorer and similar application.
Because windows is accessing the files through different user (probably)
you need to allow `user_allow_other` option in the FUSE configuration file `/etf/fuse.conf`.

```shell
echo 'user_allow_other' | sudo tee -a /etc/fuse.conf 
```


