#include <unistd.h>
#include <stdio.h>
#include <sys/select.h>
#include <iostream>

bool khbit()  
{
    struct timeval tv;
    fd_set fds;
    tv.tv_sec = 0;
    tv.tv_usec = 0;
    FD_ZERO(&fds);
    FD_SET(STDIN_FILENO, &fds);
    select(STDIN_FILENO+1, &fds, NULL, NULL, &tv);
    return (FD_ISSET(0, &fds));
}

int main(int argc, char const *argv[])
{
    int count = 0;
    bool ok = true;
    while(ok) 
    {
        std::cout << count << std::endl;
        count++;
        ok = !khbit();
    }
    std::cout << "We pushed something!";
    return 0;
}