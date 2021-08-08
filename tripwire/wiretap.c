#include <time.h>
#include <stdio.h>
#include <stddef.h>
#include <stdbool.h>
#include <sys/stat.h>
#define YR
/* Linux can represent files with stat struct using following convention */
// struct stat {
//     dev_t     st_dev;     /* ID of device containing file */
//     ino_t     st_ino;     /* inode number */
//     mode_t    st_mode;    /* protection */
//     nlink_t   st_nlink;   /* number of hard links */
//     uid_t     st_uid;     /* user ID of owner */
//     gid_t     st_gid;     /* group ID of owner */
//     dev_t     st_rdev;     device ID (if special file) 
//     off_t     st_size;    /* total size, in bytes */
//     blksize_t st_blksize; /* blocksize for file system I/O */
//     blkcnt_t  st_blocks;  /* number of 512B blocks allocated */
//     time_t    st_atime;   /* time of last access */
//     time_t    st_mtime;   /* time of last modification */
//     time_t    st_ctime;   /* time of last status change */
// };

/* Define Structs to be passed from Pyton */
struct PyStruct {
	const char* str;
	int num;
};

/*function to get size of the file.*/
long int findSize(const char *file_name){
    struct stat fileInfo; 
     
    /*get the size using stat()*/
    if(stat(file_name,&fileInfo)==0)
        return (fileInfo.st_size);
    else
        return -1;
}

/* function go check whether a file exists. */
bool fileExists(const char *path){
    // Try to open file
    FILE *fptr = fopen(path, "r");

    // If file does not exists 
    if (fptr == NULL)
        return false;

    // File exists hence close file and return true.
    fclose(fptr);

    return true;
}

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

/* return timestamp of time file was  */


/* To build shared library compile with gcc -shared -fPIC */