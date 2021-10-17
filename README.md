# TripWire 
Create a file, mark it with trip wire, and run the agent in the background. The script with
send an alert if it sees the "marked" file is open/altered. 

How to know when a file was last opened?
Linux files have useful info about them that can be accessed with the following structure. Using st_atime we can figure out the time a file was last accessed.

```C
struct stat {
    dev_t     st_dev;     /* ID of device containing file */
    ino_t     st_ino;     /* inode number */
    mode_t    st_mode;    /* protection */
    nlink_t   st_nlink;   /* number of hard links */
    uid_t     st_uid;     /* user ID of owner */
    gid_t     st_gid;     /* group ID of owner */
    dev_t     st_rdev;    /* device ID (if special file) */
    off_t     st_size;    /* total size, in bytes */
    blksize_t st_blksize; /* blocksize for file system I/O */
    blkcnt_t  st_blocks;  /* number of 512B blocks allocated */
    time_t    st_atime;   /* time of last access */
    time_t    st_mtime;   /* time of last modification */
    time_t    st_ctime;   /* time of last status change */
};
```

## **STEP [1]**: *How to know if a file was read/opened or modified from code?*
Putting these C Functions into a library called called `tripwire.c` and compiling with  `gcc -shared -fPIC -o tripwire.so tripwire.c`. 

```C
/* return timestamp of time file was last modified */
void lastModified(const char *fileName, char buff[]){
    struct stat finfo;
    struct tm * tinfo;
    // Stat file name into struct, and convert to useful timestamp
    stat(fileName, &finfo); 
    tinfo = localtime (&(finfo.st_mtime)); 
    strftime(buff, 21, "%b %d %H:%M", tinfo); 
}

/* return timestamp of time file was last accessed */
void lastOpened(const char* fileName, char buff[]){
    struct stat finfo;
    struct tm* tinfo;
    // stat file into struct and get field for last access
    stat(fileName, &finfo);
    tinfo = localtime(&(finfo.st_atime));
    // convert to timestamp
    strftime(buff, 21, "%b %d %H:%M", tinfo);
}
```

### Monitoring this over time
Here's how it looks on the commandline detecting file access and modification. 
![usage](https://raw.githubusercontent.com/scott-robbins/TripWire/master/ex.png)