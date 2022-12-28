# High Level Design

## del.icio.us

This was the name of a website launched in 2005-2006 by a student in a college and it was running on a single laptop in a dorm room. The company was eventually bought by Yahoo. So from its launch days till the acquisition, the website had become fairly large. So we will document its journey to understand the kind of challenges large systems face.

This website helped people access their bookmarks across different machines. Two main functions the website provided were addBookmark(user_id, site_link) and getAllBookmarks(user_id). All the data was being stored in the machine which was also running del.icio.us.

There is a central authority called ICANN. It is a central, non-profit entity that manages all registered domain names, tracks the registered owner of the domain, the IPs corresponding to the domain name, expiry date of ownership. ICANN makes some money by selling the domain names. The money is used to keep the machines, which are used to store the information, running. The access to domanin names usually lasts for a year. 

There are authorised resellers like GoDaddy.com or domains.google. Say, i am looking for www.kiran.com. I will go and check with GoDaddy.com. GoDaddy checks with ICANN for availablity. If it is available, then we can buy the domain name. A new entry is created in ICANN with details like the domain name, email and other details.

Machines recognize each other using IP address. It is easier for humans to remember names. ICANN was created to be the entity who stores the record of domain names and their owner.

If everyone talks to ICANN directly, they will need many machines to handle all the traffic. This is why ICANN uses resellers who does work on ICANN's behalf. They maintain a copy of a list of the most commonly checked domain names. The resellers would need to talk to ICANN only when they encounter a request for a domain name that is not in their list. This way ICANN reduces the load on its servers. 

With the domain name, we also need the ip address of the machine to talk to. In the case of del.icio.us, suppose the laptop's IP address is 10.20.30.40. The browser should know that it has to talk to the machine with said IP address. To facilitate this, an entry for the IP address against the domain name is created in the record at ICANN. One way for the browser to get the IP address associated with the domain name is to talk to ICANN. This is not a good design. ICANN becomes a single point of failure in this design. 

Imagine we have 1000 machines distributed around the world. Imagine all the machines talk to ICANN and get a copy of all the domain names and associated IP addresses. IN addition, these machines will also check in with ICANN at periodic time intervals for any updates. Now the browsers can talk to any of these machines instead of going to ICANN all the time. These machines are called domain name server (DNS) machines.

Two questions arise here. Who pays for these machines? How is delay in update handled? 

In case of the first question, there are two types of players who have incentive to maintain these machines. 

One is the internet service provider (ISP). The first step, when we access internet, is to get the IP address associated with a domain name. This IP address has to come from a DNS machine. If the ISP has to get the information from any random DNS machine, and that machine is slow, then our internet access with the ISP will be slow irrespective of the speed of the connection. So the ISP has an incentive to own DNS machines and maintain them to ensure the quality of the service they provide.

Second is players who benefit from a lot of traffic on the internet. A player like Google is so big that an indicator of their revenue is the number of people using the internet. Google's DNS machine's IP address is 8.8.8.8. Another player is Cloudflare which is a CDN. They maintain a machine at 1.1.1.1.

In case of the second question, suppose we change del.icio.us' IP address to 10.10.10.10. All the DNS machines do not know it yet. The general guideline on the internet says, if we update the IP address at ICANN, it will take about 24 hours to be updated all around the world. Spreading an update like this is called DNS propogation. 

Internet is a collection of machines that are connected in a network. All the machines have a unique identifier called IP address. These addresses are unique for the network. When a new machine enters the network, they have to be provided with a new address. Anyone can connect to the internet only through an ISP. Every ISP has a range of IPs that are allocated to them. ISPs allocate one IP address to a user. We, as a user, have the option to get a static IP from the ISP by paying an additional amount. This means everytime we connect to the internet though the ISP, they allocate the same IP to us. 

When we type in a domain name in our browser, the browser talks to the DNS machine and gets the associated IP address. Then the browser talks to the machine at that IP address to access the content in that domain.

When we change the code running in a machine associated with a domain, how do we make sure that the updated code is the process running? We will have to kill the current running process and start running a new process. There will, presumably, be a gap of few seconds between killing the old process and starting the new one. In that gap, people will not be able to access the website. How do we solve this? 

A solution is to have multiple machines instead of just one. These multiple machines will all have similar running code and their own database which will have the same records. We have to make sure that when we are restarting the process in one machine, no requests come in to the machine. We have to use a load balancer to solve this. So the IP of this machine is the one associated with the domain. When we deploy new code in a machine, we have to tell the load balancer to stop sending requests to that particular machine. This is the purpose behind having multiple machines which is to ensure continuous availability. To prevent the load balancer from being a single point of failure, we can have standby load balancers that will take over with the same static IP in case of failure.

A load balancer need to maintain a list of machines it has to send requests to and their status. The load balancer can employ any algorithm to ensure the requests are spread between the machines. One algorithm is the round robin. It will send one request at a time to each machine in a circle. The load balancer can keep track of the health of the machines using two mechanisms called heart beat mechanism and health check mechanism.

In health check mechanism, the load balancer has to go and ping these machines. For example, we can ping using HTTP at port 8080 at path "/". We can ping every 30 seconds and wait 5 seconds for a response. We can set a fail threshold at 2, where if the ping fails twice consecutively, then we can assume the machine is dead.

In heart beat mechanism, evey 30 seconds, all machines have to tell the load balancer that you are alive. Load balancer keeps listening but does not go and check. If load balancer does not hear from a machine in a 1 min interval, it will assume the machine is dead.

Zookeeper keeps track of load balancers.

Other algorithms load balancers can use to route requests are ip hashing, least active connection. IP hashing is especially useful for feature testing.

Let us say del.icio.us has become so popular that they add 1 million bookmarks everyday. Every record is a user_id and url which is about 250 bytes. Everyday about 250 MB of data is generated. If the current space is 40 GB, then we would run out of space in 160 days. We could get machines with increased space capacity. This is called vertical scaling. There is a limit to vertical scaling because there is a limit to storage capacity in a single machine. Alternatively, we could add more machines and split data between machines. This is called sharding. This means all machines dont store all data. Some of it goes to first machine, some of it goes to second machine and so on. As existing storage space fills up, we can add more machines and split the existing data among all the machines. Hence there is no upper limit in capacity with this design.

How do we split the data among machines? if one user's data is split among all the machines, then when the user wants to access all their data, the load balancer will have to ask all the machines for data corresponding to the user. So, time to get data is long and hence is not a good design. One solution is to store all data corresponding to a user in a single machine. Before splitting the data, we group the data by user_id and then we split the data user wise among all machines. In this case, we are using the user_id as a sharding key. Every information related to the user_id will stay together and will not be split among multiple machines.

Some questions that arise here are

1. How do we prevent load skew?
2  How does the load balancer know which machine to go to when it recieves a request?

First we will answer how a load balancer can know which machine to go to. There are a few guidelines.

1. It should be easy for the load balancer to match user_id to machine while being lightweight.
2. There should not be any load skew. 
3. If we add/remove machines, things should still keep working.

First approach is to identiy the machine by computing user_id%number_of_machines. Consider some user_ids and 5 machines
```
        user_ids            |               Machine
           10                                  0
           14                                  4
           18                                  3
           21                                  1
           26                                  1
           30                                  0
           23                                  3
```
This approach will not have a load skew if we consider many users and all users have a similar frequency of accessing the website.

Now suppose the storage capacity of these machines is close to full and we add one machine to increase capacity. Now the data of close to all the users will have to be transfered to a different machine because the user_id%number_of_machines will result in a different machine number. If we employed this approach when storing terabytes of data, everytime additional storage capacity is added, the data will have to be transfered, which will take a lot of time. Hence the 3rd condition is not being satisfied in this case.

If we kept a hash table of user_id and machine number in the load balancer, then while conditon 2 and 3 will be satified, condition 1 will fail because the load balancer is not lightweight anymore. Lightweight means the number of cpu cycles being used and the memory consumed are both less.

Second approach could be store data of users in different machines based on the range the user_ids fall into. Machine 1 stores data of users whose user_id falls in the range 1-100, machine 2 for range 101-200 and so on. Condition 2 gets violated here as there could be skewness. The oldest users with user_id in the range of 1-100 may be relatively active users and generate far more data than the recent users. Another issue is that the users do not get redistributed to new machines. So as the existing users keep generating new data, the storage space in that machine will get filled to capacity. So, due to these two issues, this design is not appropriate.

Third approach is called consistent hashing. Consider a hashing function that takes a machine id as an input and returns a hash value. Hashing funnctions always return the same value for the same input. Our hashing function is designed to provide a value between 0 and 10^18. Consider that we have 4 machines to store data in. When we input the machine id into the hashing function, we get a hash value. The hash values are stored in an array which is sorted. We have another hash function which take user_id as input and returns a hash value. This has function also returns values in the range [0, 10^18]. When a user request comes into the load balancer, we get the hash value for the user_id. We locate, using binary search, the two adjacent indices between which the user_id hash value lies. Once we identify the machine represented by the hash value in the latter index, the load balancer will direct the user request to that machine. This approach of sharding is called consistent hashing. 

Storing the machine hash values in an array will not consume significant memory. Calculating the hash value of a user_id for every request will not consume significant CPU cycles. Performing binary search is an O(logN) operation, and hence will not consume significant CPU cycles. Hence the entire process is lightweight. So we satisfy the first condition. There is a small probablity of two hash values of machine ids being close to each other. This will result in load skew. So the second condition is not satisfied. If a machine dies, then all the traffic to that machine gets diverted to the machine located next to it in the hash value array. The load on the latter machine doubles and hence it could fail too. If this happens, then all the traffic to this machine gets diverted to the machine located next to it in the hash value array. The load increases 3x which means this machine could fail too. This is known as cascading failure and it ends with all machines failing. Hence the third condition is also violated.

We need to modify consistent hashing slightly to make it work. Instead of generating one hash value per machine, we will, lets say, 3 hash values per machine. This means we have three hash functions for generating hash values based on machine id input. We arrange these hash values in a sorted cyclic array. 

```
M1  |  M3  |  M2  |  M4  |  M1  |  M4  |  M2  |  M3  |  M1  |  M2  |  M4  |  M3
```

The hash values array is now bigger than the previous approach. However this array will still not consume significant memory in the load balancer. Performing binary search will still not consume significant CPU cycles. So modified consistent hashing satisfies the first condition. There are more hash values per machine than one. Hence the distribution of users across the machines will be better. So, this modified method scores better than the previous one on the second condition. Fo the third condition, we will first check what happens when we remove a machine. When a machine dies, the traffic to that machine gets distributed among more than 1 machine with the modified method. For example if M3 dies, the traffic to M3 is now diverted to M2 and M1. The load on a single machine will not double and hence there is a smaller chance of failure. With more hash values per machine, the distribution when a machine dies gets better. When we add a machine, then we insert new hash values at difference locations in the array. So some users, not all users, of previous machines gets added to the new machine. So all users are not affected, only some are. Addition of a single machine reduces the load per machine across the board. 

How are the users migrated from the old machine to the new machine without any downtime. It happens in two phases. Phase 1 is, we know that we have to add a new machine. But we do not immediately add it to the array yet. Before we add the new machine, we copy the relevant users data from the current machines to the new machine starting fro timestamp T1 to T2. The new machine will not have any new updates, to the users data, that happened between T1 and T2. 

If we are building a highy consistent system, when we add the new machine to the array at T2, we go to all the machines and copy the delta data. This process lasts from T2 to T3. Between T2 and T3, we fail any request that comes in for these users in the delta data. Post T3, we start handling requests for all users. This way, we stay consistent.

If we are building a highly available system, we will handle any requests that come between T2 and T3 even if the data is not yet consistent.

A hash function that can generate multiple has values for the same user id will look like this
```
hash(user_id, hash_no) {
        hash_hash_no = fn(hash_no);
        new_inp = combine(user_id, hash_hash_no);
        hash_val = hash_fn(new_inp);
        return hash_val;
}
```

## Hardware vs Software Load Balancer

What we discussed above is hardware load balancer. 

If a request that comes needs to be routed to different services, then we need a software load balancer to route the request to the appropriate service. It is also called reverse proxy or gateway.

## Caching

Is it a good model to have the business logic and data store to be running in the same machine? No, because, when there is tight coupling between code and database, whenever there is code deployment, the new code is copied to the system, the existing process is killed and new process is started. During this phase, the machine does not take any new requests. The users who have data in that machine will be able to access their data. If we deploy code frequently, then those many number of times, data of certain users will be unavailable. Upgrading DB will also cause unavailability.

There are two types of processes, either memory intensive or CPU intensive. DB is a memory intensive process. If code and DB tightly coupled, then there are fewer resources related to memory left for the code.

So now we split code and database into different machines. Machines with code are called application server machines. If all these machines are running the same code, and a request comes for user number 1, then it does not matter which appserver the request is sent to. These kind of systems are called stateless systems. 
```
Number of appservers = Peak QPS / Number of queries a machine can take
```
It is easy to implement autoscaling with appservers.

When we cache data in appservers, they become stateful systems. Then we cannot send user requests to any machine. It will be sent to the appserver that has cached the particular user's data.

Each appserver should know which database to talk to when a request comes in. Typically all database systems have a client operating in the appservers. These clients implement consistent hashing. When the client is instantiated, it talks to the cluster manager to get the metadata like the number of machines operating, the number of hash functions etc once. Then they run consistent hashing process independently to determine the machine to send the request to. What was happening in the load balancers earlier is now happening on the appserver. In practice, load balancers do not do consistent hashing because we usually do not have the application layer and the database layer in the same machine.

In case the number of machines/number of partitions are fixed, then we can do modulo number of machines operation to split user data. However, if the number of machines are not fixed and we want the flexibility to add machines when we want to relieve the load on the existing machines, then consistent hashing is the right choice.

Each appserver should be aware of the active database machines, number of machines and the number of hashes. The number of hashes does not change, but the number of machines could change. Zookeeper helps the appservers keep track of this data. Internally the database client keeps track of the machines through the zookeeper.

Let us recap the steps from typing in del.icio.us in the browser.

1. DNS lookup
2. Establish connection with load balancer
3. Load balancer sends request to appserver.
4. Appserver has to fetch images or list of bookmarks

How can we make the experience faster for the user? 

We start from the first step. Do we need to use the DNS everytime to get the IP address? Browsers have local storage. We can store cookies (key, value) or session (mini database). Maybe we can cache IP. The system of storing data in a faster but smaller storage system is called caching. The first place we can start with caching is the browser. What data can we store in the browser so that we do not have to go to the server side to fetch? To save time, we can store some IPs in the browser so that we do not have to do DNS lookup everytime.

Use in-browser caching.

If the load balancer is in the US and we are in India, then transfering data between the browser and the load balancer can take a lot of time, expecially if there are images that are a few MBs in size. One way is to first transfer only HTML code, which is text and small in size. This HTML code will have links to images. If we can have machines all over the world, then we can store these images in all the machines. The links that are embedded in the HTML code can then be a link to get the images from a machine that is located closest to us. This will reduce the latency in transferring relatively large size multimedia content. 

However, owning and maintaining machines all over the world will be expensive. Hence a service called content delivery network (CDN) was born. The CDNs provide this service of maintaining machines all over the world and storing your data in them for a fee. This way we can embed the CDN links for images in the HTML code and hence reduce latency in fetching images. 

How do the browsers get the IP address of the machine located close to us rather than one of a machine located farther away? There are two ways. ISPs have CDN integrations. Which means the CDNs tell the ISPs that if you get a request from a particular location, route it to the IP that is located closest to the particular location. In the second way, CDNs redirect based on origin. The header of the request will have point of origination. If a request goes to a machine located far away, it will look at the header of the request and redirect it to a machine located close to the origin if required.

Using CDN is caching.

Reading from a database across the network also takes time. We can cache data in-memory in the appserver to reduce this latency. This can include derived data as well. In this case, we do not need to compute to get the data.

Any form of cache is limited in size. It is not the actual source of truth. There are two issues with this.

1. Stale data. 
2. Cache is full.

We need a cache invalidation strategy to prevent the data from going stale.

1. TTL - Time to lift. If we are okay with some period of inconsistency, then we can go for periodic refresh. For example, we can say that the IP address for del.icio.us stored in the browser cache is only valid for 1 hour. Post the time to lift, we have to go and fetch the data.

2. For cache in the web server, we can employ a write-through cache. Any data we need to write to storage, we first write in cache and the cache itself will try to update the DB. If both are successful, we can return success. If DB write fails, we revert the entry in the cache and return. This ensures consistency between data in the cache and the DB. This will make the writes slower, but the reads much faster.

We can also employ a write-back cache strategy. New data is updated in the cache and we return success. The cache is later synced with the DB. This can result in inconsistent data between cache and DB. We can also lose data. This strategy is typically employed when we can afford to lose a small portion or small chunks of data. Latency will be low and throughput will be high. This is typically employed in analytics where we can more about the trend of information.

In a write-around cache strategy, the DB and cache are always out of sync. So we employ cache updating strategies like TTL to make sure that cache is able to invalidate regularly.

We need a cache eviction strategy when our cache becomes full. 

1. FIFO strategy
2. LRU strategy
3. MRU strategy - COWIN, most recently downloaded vaccine certificate.

Eviction strategy depends on data access pattern. There is no one size fits all.

When we want to fetch an entry, we first check in cache. If it is present in cache, then it is called cache hit. If not, it is called cache miss. We want to employ a strategy such that we have a high cache hit/cache miss ratio. This has to be optimized with the time taken for responding to a request.

## Local Cache Case Study

In order to evaluate our code submissions, Scaler needs an input file and an expected output file. Input file is used to feed input into the code that we have submitted. Expected output file is used to compare output from our code to the expected output to judge the correctness. Scaler stores these files in a file storage which is a seperate machine. Assume it takes a 1 second to fetch one file from the file storage to the appserver, which is where our code is evaluated. So the whole process can take about 2 seconds. Assume this is too slow and we as users will be unhappy with the time taken by Scaler for evaluating one code. How can we speed up the process? Now assume we can query a DB machine in 40 ms and the HDD in the appserver machine in 10 ms. 

The obvious solution is to store the files in the HDD of all the appserver machines. There is a constraint that arises here. In case we need to make changes in the input or the output file, we will have to go to all the appservers and make these changes. Whats the efficient way to perform a cache invalidation strategy?

Let us first discuss two possible alternatives.

1. TTL. Here, we sync the input and output file between the appserver and the file storage. If we choose an interval time of 1 minute, then Scaler may experience several cache misses because, every minute the cache will be unavailable due to the sync process. If we choose an interval time of 60 minutes, then there will be a period of time for a particular problem in which the evaluation will be erroneous. 

2. Maintain a global cache. We assign a machine where we store the data in its RAM. The RAM could be insufficient to hold large file. Even if we have a large enough RA, there is a risk of the cache machine being unavailable.

The third solution is to store the metadata of the files in an SQL DB. The metadata will contain columns like problem_id, input_file_path, output_file_path, input_last_updated_timestamp, input_created_at_timestamp, output_last_updated_timestamp, output_created_at_timestamp. In addition to this, we store the files in the HDD of the appserver with specific names like problem_id_last_updated_timestamp_input_file. When a request for code evaluation comes in, we use the problem_id to get the metadata record from the SQL table and construct the file name. If the file_name is present in the cache, we proceed with code evaluation, else, we fetch the updated files from the file storage and store it in the HDD of the appserver. This is a clean way to use local cache when there is a requirment to update the cache.

## Case Study Scaler Ranklist

Consider a contest by Scaler. In a contest, some of us may look at the list of problems, others may be submitting code and some others may be looking at the ranklist. If there is a lot of traffic and scores are being updated freuqently, then computing the rank list may be expensive because we have to go to the database and sort based on score. This will cause a lot of load on the DB and sorting the table may also be slow. So Scaler decides to show the ranklist with a lag of 1 minute. Every 1 minute Scaler update the ranklist to reflect the latest scores. Imagine if Scaler cached the ranklist locally in the appservers and assume they have 1000 appservers. This will result in 1 cache miss per server per minute. Instead of a local cache, Scaler keeps a global cache. All the appservers can talk to the global cache. The global cache keeps a copy of the ranklist with a TTL of 1 minute. Now there will only be 1 cache miss every 1 minute as there is only 1 machine. Local cache, in this case, was not a good solution as opposed to global caching. Global caching has a higher cache hit/cache miss ratio than local caching.

## Redis

Redis is a popular global caching system. It is a single threaded key-value store.
The value data types that redis can take are string, integer, list, set, sorted-set.

We use global caching for couple of reasons. 

1. Quick access to a field or entity that is queried often.
2. Easy access to derived/precomputed information that might be expensive to compute on DB.

We do not usually store files or bulky pieces of information. 

When do we use caching? To answer this, let us look at a world with caching and a world without.

In a world without caching, we will query the DB for data and respond to a request with it. Imagine this takes 10 ms. 

In a world with caching, we will first check the cache for the data. If available we will respond to a request with the data. This take 5 ms which is faster than querying a DB. But if we do not get the data from the cache, we will have to query the DB which takes 10 ms again. So, in case of a cache miss, we will take 15 ms to responnd to a request. 

So, caching works when we have a high hit rate and reduce the cache miss rate. This means that we want to store the most relevant things in Redis. If an item is being queried only once a day, then we do not need to use Redis.

A way to store a rank list on redis is to have sorted-set of (score, user) and every time a score is updated, we go and change it in the set. However, this an expensive operation and increases the load on redis.

In a redis list we can get values from index X to index Y by running a command called LRANGE(X,Y).

## Case Study Facebook

Facebook has users. A user has a bunch of attributes like id, name, email, relationship_status, last_active. Users also have friends. So that will be a table called user_friends which will have user_id and friend_id. Users can also make posts, so we will have a posts table with attributes like id, text, user_id, timestamp etc. There are two types of pages that we can see on facebook. One is the newsfeed and other is a profile page of a user_id.

The profile page of a user_id will show name, relationship status and posts made by the user. Newsfeed has posts made by friends of user_id.

If all of the data was stored in a single machine in a DB, then we can query the Db to get the information to display on profile page and the newsfeed.

For the profile page, we can run
```
SELECT * FROM posts WHERE user_id = <user_id>;
```

For the newsfeed, we can run
```
SELECT * FROM user_friends JOIN posts ON a.user_id = <user_id> AND b.user_id = a.friend_id AND b.timestamp >= NOW() - 30;
```

But we cannot fit all the users data in a single machine. We have to shard the data.

What is my sharding key? On what attribute do we shard?

Let us say we shard on user_id. The data that one user has are user attributes (entries in the user table corresponding to user's id), list of friend ids, posts made by the user. The entire data for each user will be sharded into multiple DB machines.

Computing the profile page is still easy because we can find a user's profile page data in one machine. However, computing the news feed will now be expensive. We have to collect a user's friends' posts from different DB machines and this is computationaly expensive. How do we optimize the newsfeed?

One approach is to cache user as key and posts as value. The posts are not just posts, but actually the content of posts. There are a few problems with this approach.

1. This design will require a lot of space. Facebook has about 2 billion users and we have to save about 1000 posts for every user and every post is say 100 bytes, then we need about 2000 billion * 100 bytes = 200 TB (a billion bytes = 1 GB) of space. We need about 200 to 300 machines just to cache the posts. 

2. Another problem is updating the newsfeed of all the user's friends with a post that the user made. If the user has about 1000 friends, then we need to be 1000 updates. 

3. If we change the newsfeed to now include posts of friends of friends, events, pages etc. then this design presents a problem. Changing the newsfeed algorithm now becomes difficult.

In this design, we would be storing the same post multiple times against different users. If we do not store duplicates of a post, then what could the size of all posts required for a newsfeed be? 

Facebook has about 3 billion users, of which there are 1 billion users who are active a few times a month, of which there are 500 million users who are active every day. There is a rule of 80:20:1 rule in the context of any social media. 80% of users only consume content. 20% of users interact, make some comments etc. 1% of users actually create posts/content. So about 5 million people make a post a day. So we are dealing with 5 million posts a day. If every post is about 100 byte, we are looking at 500 MB of posts every day. If we want to store only those posts that were made within a month, then we need to store about 15 GB of data at any point of time. Lets assume 4 times this amount and say we need to store about 60 GB of data at any point of time.

This means we can store this data in an HDD. Lets say we decide to fit this data into a single machine and designate it as the global cache for storing posts of the last 30 days. If every other machine in the local network talks to this machines, it will become overloaded. So, we make a lot of copies (about 100) of this machine to prevent overload. 

To compute a user's newsfeed, 

1. We need the user's friend list. So, we will first go to the DB machine where the user's details are stored and get the friends list.

2. Then we go to the global cache and run
```
SELECT * FROM all_posts WHERE user_id IN friend_ids LIMIT 100;
```
Now, when we update to write a new post, we, only need to do 2 writes. One in the global cache and the other in the DB machines which store the user details. The new post is then propogated to all the copies of the global cache at its own pace.

Every day, we run a job in the global cache to delete posts that are older than 30 days.

How is REDIS fast inspite of being single-threaded?

Multi-threading has 2 issues.

1. When multiple threads attempt to access a key-value pair, a lock is taken to avoid race condition. This causes a few nanoseconds delay which might not seem like a lot, but has an impact on the performance of a system.

2. Context switching. When a process is executing, then there is a context associated with it. If something else that is important crops up, then the CPU dumps current context somewhere else and picks up this new task. This is expensive and is more likely to happen in a multi-threaded environment.

REDIS avoids all this by staying single-threaded.

How do you choose between local and global cache? In most cases we choose global cache. A general rule of thumb when it comes to local cache is to employ it when we have large amount of data, which makes it expensive to transfer it over the network and the file is not updated often. A caveat to global cache is, when consistency of data is a strong requirement, and we have to employ a write through cache and there is a fair bit of application logic on the caching front, then we might make the appserver stateful and store things in it which makes appservers also specific to users.

System design has two parts

1. Architecting - Given a problem statement, what are the components that should exist that reduces the risk of error, the risk of system going down, the risk of losing information. 

2. Solutioning - Once we have a solution in place, then identifying technology/software in the market that can serve the particular need is solutioning. 

Architecting is the harder skill to develop. Once developed, solutioning will come easily. Understanding the tradeoffs, the pros and cons is trickier.


## CAP Theorem

We will look at a new case study. Consider a service that saves reminders for users over the phone. We registered a phone number and told potential users that they can call the number to either save a reminder or retrieve a reminder. Currently, we have one operator who saves reminders in a diary. Suppose we add another operator who also saves reminders over the same phone number in a different diary.

One day, a user calls up to retrieve a reminder, but the operator was not able to find the reminder in their diary and hence could not respond to the request. The operator could not find the reminder because the call to save the reminder was handled by the other operator who had saved the reminder in their diary.

How do we avoid these kind of issues?

1. We could maintain a common diary. This has its own set of issues. When the diary is being used by one operator, the other operator will not have access to the same diary. Operators may make entries related to the same reminder in different pages.

2. We can develop some protocols to maintain consistency between the two diaries. When we receive a request to save a reminder, we ensure that the reminder is saved in the other diary as well. We return success only when the request is saved in both diaries. The tradeoff here is a a delay in response or increased latency. This cannot be avoided. 

We have solved the consistency issue by implementing a protocol to replicate the data across diaries.

In case an operator is not available for a period of time, we cannot implement the protocol. There a few ways to handle this issue.

1. We can stop taking new requests until the operator comes online. Availability takes a hit because of protocol/consistency.

2. One operator can continue handling requests and saving them in their diary. When the other operator comes online, they sync the data in the diaries until both are up to date.

In case the two operators stop talking to each other. In the duration that this happens, the system becomes inconsistent. Suppose the two operators stop talking to each other at time T1. At time T2, a user calls to retrieve a reminder that they saved with operator 1. The call at T2 goes to operator 2. Operator 2 will not be able to serve the request. At this point in times, the system is available, but not consistent. 

In case of a network partition (both operators talk to outside world and each other seperately), we can either choose availability or consistency.

CAP theorem says that, in case of a network partition, if two nodes are not able to talk to each other, but they are able to talk to the internet, we have to choose between consistency and availability.

## PACELC

In case of a network partition, we have to choose between availability and consistency else if there is no network partition, we have to choose between latency and consistency.

We saw the example of when the two operators are not able to talk to each other, we have to choose between availability and consistency, however, if they are able to talk to each other, then we have to choose between consistency and latency. 

Suppose a request to save a reminder comes to operator 1, and the protocol is such that when the operator saves the data in their diary, we return success without waiting for it to be written in the other diary as well. This system has a great response time (low latency) but takes a hit on consistency, because the user could call operator 2 for retrieving the reminder before it has been written to the operator 2's diary.

## Replicas and how to sync replicas

In consistent hashing, we sharded the data into multiple machines. So each machine holds shards of data. If we operated with a single machine for each shard, they are all single points of failure because if a machine goes down, we will lose that shard of data. So each shard has to be replicated into multiple machines or a cluster.

This is known as master-slave architecture. The machine to which all writes go to is called master. The machines that are replicas of the master are called slaves.

We can design our system as wither highly available or highly consistent. In case of highly available, we can choose between our system being eventually consistent or have very low latency.

Let us explore each choice of system design.

1. Highly available, low latency

a. Master takes writes and return success if success.
b. Asynchronous best try to sync data on slaves. Even if we lose a portion of the data, as long as the distribution is maintained, we are good to go.

2. Highly available, eventually consistent

a. Master takes writes and one slave writes and returns success.
b. All slaves sync. Gossip protocol.

3. Highly consistent

a. Master and all slaves write. If success, return success. We do not use the gossip protocol here as master has to write the data in all slaves.

Some of the cons with highly consistent design is that latency will be high and availability could be impacted. Even if one slave fails, we have to return failure.

It is generally advised to avoid keeping 1000s of slaves for each shard. A possible reason to keep many slaves is to delegate the read requests to slaves. This is particularly useful in a read heavy application.

In case a master fails, in the highly available, low latency design, we can make any slave the new master. In the highly available and eventually consistent design, we track the slave with the most up to date information. This slave will be the new master. In the highly consistent design, every machine is eligible to become a master.

Delta sync helps in keeping the system available and become eventually consistent. Lagging delta machine will ping leading delta machine multiple times for data until there is no more data to return and both machines are in sync.

## SQL vs NoSQL

ACID - When we want to withdraw Rs 500 from a bank, we want the transaction to be an atomic operation. This mean there should not be any inconsistency. We have to check if there is sufficient balance, and debit in case there is sufficient balance. All this has to happen in a single transaction and not in two phases.

In SQL,
```
UPDATE account SET balance = balance - 500 WHERE user_id = <user_id> AND balance >= 500;
```
This operation is executed as a single transaction.

SQL also allows us to join tables and compute analytics and other information, all through single transactions.

Imagine there is an ecommerce system like Flipkart. Flipkart has a lot of different types of items. They might be selling t-shirts, MacbookPro, Nike and many such products of thousands of categories. Each category (SKU) can have different parameters. For t-shirts, the attributes can be gender, size, collar_style, colour etc. The attributes of Macbook Pro will be entirely different as compared to t-shirts, both of which will be entirely different to shoes. How should we store this in a DB?

We could have a table called items with three columns called item, category, properties. Properties will be stored as a string. To give an example, 
```
Nike    |       Shoes       |   "{type:sneaker,colour:black,....}"
```
The problem with storing information like this that filtering for specific items become expensive. If we want to get all shoes that are black, we could run something like
```
SELECT * FROM items WHERE category = "Shoes" AND properties LIKE "%colour:black%";
```
The % symbol acts exactly like the wildcard character. This is going to be a very slow query because it will go through every row and perform string matching. This is because we cannot do indexing in this. This type of search is called full text search.

This operation has a time complexity of O(N)*O(string comparison). Filtering on the table will take a long time, especially when we have hundreds of millions of items. This will not scale unless we operate with multiple machines in which case, we can never turn a profit.

In case we store items in tables for each category. We will end up with thousands of tables that it will become hard to even keep track of the tables.

For an ecommerce use-case, SQL does not work well for storing products because schema is not SQL friendly.

Challenges of SQL

1. E-commerce - schema is not SQL friendly. This could still work if all the data was on a single machine using JOINs. But the moment we split the data into multiple machines, even JOINS will not work.

2. Power of SQL queries is reduces when information is across machines. 

When we store data in multiple machines, we have to denormalize it. Taking the facebook example, we can have users table, user_friends_table and posts. table. This is possible when all the data is on a single machine. However, when we split the data into multiple machines, then we will need to store user1 and store all of user1's friends which will include user2. User2 will be on a different machine where we will also store user2's friends which will include user1. So we can get the friend list directly from a user's record which helps to reduce latency at the cost of redundancy.

3. Most SQL machines, out of the box, are not built for sharding. Some enterprise versions of some SQL machines support it like Oracle

We need a solution that supports the e-commerce schema and has a built in support for sharding. Every single benefit of SQL, ACID included, goes away the moment we shard data. For example, if there is an update to be made across users, we cannot guarantee that multiple machines will updated atomically and that they will be isolated and consistent. So we need something that works well in a sharded infrastructure.

## Sharding

### Designing a sharding key

When we know we have to split the data across machines, what should be our sharding key? How should we decide what data goes to which machine? What is the framework to follow?

First step is to list down the common queries for a use case. For example, in a banking system, we will have the following use cases

a. Check bank balance
b. Credit money (account_no, amt)
c. Debit money (account_no, amt)
d. getHistory (account no, start_date, end_date)

Account no is a common parameter in all the use cases. 

There are some cases where we could have multiple candidates for sharding key. For a messaging system, there are queries with respect to a conversation_id (latest message in conversation, last 10 messages of the conversation), some others could be based on user_id (recent conversation of this user, search mailbox). In such cases, we will have to compare the behaviour of our system when we choose one attribute over the other. The least expensive one becomes our sharding key.

Some of the examples are Uber, IRCTC and Slack, youtube.

## Schema

Imagine we have sharded by user id. Now we have to choose the way to store each data shard inside a machine. We could store in a table-row format or a key-value store etc. The schema will depend on the use case. RDBMS stores data in the table-row format. However, in the NoSQL world, there are broadly three types of schemas. 

1. Key-value (Hash Map)
2. DocumentDB (JSON)
3. Column Family store

Key:Value is exactly what is sounds like. We have a key and a value. Both are usually strings. It is like hash map.

DocumentDB is unstructured. We can can create any JSON object and we can store it in the DB. If we want to store details about a shoe, we could create a json like this
```
{"type":"shoe",
 "colour":"black",
 "size":"9",
 "brand":"Nike",
}
```
We can have nested structures in the JSON as well. When we want to query black shoes, then we run
```
db.query(type:shoes, colour:black)
```
This kind of DB can still have indexes and the fetches can be fast. There is no defined schema here. All entries can have different keys and values.

Let us talk about gmail. One users mailbox will be very different from another user's mailbox. A user will see a list of email threads. For a given thread, we can see emails in this thread. 

When a user opens gmail, they will see the list of recent and unread email threads. When we click on an email thread, we want the list of all emails in the thread. 

If we store the mailbox in a key-value store, we will have to store all the emails in the value as one large string. If a user's mailbox is about 100 GB, then the value will be 100 GB. This is intractable especially for the use cases mentioned above.

If we store the mailbox in a documentDB, which means every single email is a document. The way we query and unread email is
```
db.query(user_id:X, unread:true)
```
However, getting the recent threads is a challenge. We will have to get all the unread emails and then sort them by timestamp, which is expensive. DocumentDB itself will not sort for us.

In this case we have sharding key which is user_id. Let us call this row_key. Everything we are going to store in this row_key is called column families. Column family can be considered to be like a list. All the entries in a column family are by default sorted on timestamps. We can also add prefixes on each entry in a column family. When we query for the recent 50 email threads, only the 50 email threads are read. Rest of them are not read. So it is efficient. We can also query for all entries that have a specific prefix. The rest of the entries which do not have that prefix will not be read. 

DocumentDB is good for fragmented schemas. ColumnFamily storage can have lot of entries in a column family and it is easy to read filtered data based on timestamp or prefix. If there were GBs of matching data in DocumentDB, then storing that in a column family storage will be better.

Problem statment

We have to design a database where 

1. All information does not fit on a single machine.
2. We dont want to manually balance the load. We give a set of machines in a cluster to the DB and somehow the DB has to balance the load.
3. When the load goes up, add more machines into the cluster. DB has automatically balance the load.
4. DB should never lose information.
5. We can specify consistency vs availability. We can even specify somewhat consistent and somewhat available.

## Replication Level

If we want our database to store a large amount of data and serve a large number of users, is it a good practice to keep all the data in one machine? No, because we will have a single point of failure. In scalable databases, data is replicated across multiple machines. The number of machines data is replicated to is called replication level. For example, Scaler has data on the number of classes attended by a user. Lets say one machine contains this data of 5 users. Whenver this data is needed, this machine will experience load because this is the only machine that contains this data. This becomes a bottleneck and a single point of failure. 

Instead what a database system should do is to have a master machine. Master machine get writes of data. There are other machines that replicates data of the master. These machines are called slaves. If we want a highly consistent system, replication should happend immediately. If we want a highly available system, replication can happen after sometime. In this architecture, all the write requests go to the master and all the read requests go to the slaves. Now when there is traffic, any single machine will not experience significant load. If master dies, one of the slaves can promote one amongst themselves to become the master using leader election algorithms.

In SQL databases, we have read replicas URL and write replica URL.

In NoSQL databases, there is a manager/layer that sits over the real database. All the queries first go to the manager. The manager passes all the write queries to the master and all the read queries to the slaves. This why we prefer using NoSQL databases for high scale purposes. 

1. How will we ensure a particular replication level that can serve large loads and to handle failures?

2. How do NoSQL machines increase/decrease number of shards automatically? How do they scale automatically? How does data migration when scaling up take place?

Assume there is a huge amount of data, in order TBs and PBs. Also assume that there are a huge number of read requests for the data.

To handle the huge amount of data, we will need to break the data into shards and each shard will be stored in multiple machines, each of which are masters. To handle the huge number of read requests, each master can have replicas which will hande the read requests.

There is another approach called multimaster setup.

Let us discuss the master-slave architecture.

Assume we have 15 machines. Based on the load, we divide our data into multiple shards. To allocate shards to machines, we use consistent hashing. There are 2 types of queries, read and write. The queries go to the manager and based on the sharding key, the manager sends the query to a particular machine. 

In a distributed system, we can set the replication level. Replication level is the number of distinct machines that have a copy of the data. If we set a high replication level, the number of machines are high, the network usage will be larger, so we might have a slower system. This is the amount of redundancy that we have. 

The defaut replication level should be 3. What happens if we have 2? One  will be the master and the other will be the replica. If any one dies, the other one will experience a huge load and has a high chance of dying as well. If there are 3 machines, even if one dies, there 2 machines to share the load. 

SO we set sharding based on consistent hashing and the replication level at 3. 

Now, we have three masters and each master has two slaves. When queries come to the manager, write queries are sent to master and read queries are sent to the replicas.

We started with 15 machines and now we have 9 machines in use. Six machines are free. A shard requires 3 machines, so we can create two shards. However, we create one shard and leave 3 machines as reserve. If the number of machines <= number of machines required for a shard, then leave the machines in a reserve. 

If a machine that dies is from a shard that has number of machines > replication level machines, then we dont do anything. If the machine is from a shard that has number of machines = replication level, then use one of the reserves and move the extra machine from one shard to the other. 

When a machine dies, a reserve will be added, then leader election will happen and some other machine becomes a master. 

When should we add a new shard? When any existing shard gets greater than 66% usage, the manager will automatically start a new shard. 

How is a new shard introduced? There are 2 stages

1. Staging stage

a. New machines are created. 
b. Data is copied from the earlier shards to these new machines.
c. The part of data which now belongs to the new shard based on consistent hashing algorithm. The data is copied from real replicas of other shards.
d. New read and write queries are still being served by the earlier shards.

2. Live stage

a. New shard starts serving queries.

At T0, manager created a new shard. T0 to T1 is the staging stage. During this time, data supposed to belong to old shard will still be written to the old shard. At this point, the choice of action depends on whether we want a highly consistent system or a highly available system.

If we want a highly consistent system, we will take a small downtime from T1 to T2 during which we will migrate the remaining new data to the new shard. If data transfer in T0 to T1 took 40 minutes, this data transfer will take about a minute. During this time, users that belong to the shard will be impacted.

If we do not want consistency, the new shard can start serving requests while asynchronously getting new data from other shards. 

Whenever any write query is processed by the database, a commit log/transaction log is updated. The replicas use commit/transaction log to do work. This log is maintained in all the machines.

## MultiMaster Architecture

The master-slave architecture is useful when we have a system that gets many read queries, and fewer write queries. When we have a system that also gets a lot of write queries, the master-slave architecture does not facilitate an optimal use of resources.

For a use case that has many writes and many reads, one approach is to keep shard size small and have several shards. This will likely be less efficient and cost a lot. 

Another approach is to store data in the first three unique machines to the right of the users hash value. Assume we have 4 machines M1, M2, M3 and M4. There are arranged for consistent hashing in the following way.
```
M1  |  M2  |  M1  |  M3  |  M3  |  M1  |  M4  |  M3  |  M4  |  M2  |  M4  |  M2
```

If a user's hash falls between the index of M2 and M1, then the user's data will be written to M1, M3 and M4 in that order. These machines will also serve reads for the same user's data.

The con with this architecture is that write queries will become slow as the data needs to be written into three machines.

### Tunable Consistency

DB systems like Cassandra offer a feature called tunable consistency that helps mitigate the above con. Using this feature, we can tune the consistency of the system as per our preference. We can set the number of machines to read from before sending data. We can also set the number of machines to write to before declaring write query successful.

Number of machines to read from = R.
Number of machines to write to = W
Replication level = X

If R+w>X, system is consistent. 
If R+W<=X, system is available.

If the application has more number of read queries vs write queries, then we should set R smaller than W.
If the application has more number of write queries vs read queries, then we should set W smaller than R.

## Framework - Case Study

1. Requirements Gathering - Minimum Viable Product (MVP)
2. Estimate Scale - Read vs write heavy - sharding? - how much replication? - QPS
3. Design goals - Highly consistent system vs highly available - Highly available which will be eventually consistent - Latency?
4. APIs - How is the external world going to use the product? System Design - storage vs cache - what kind of appServer - Other machines to do other stuff.

### Requirments Gathering

If people want to use our product with basic minimum features, then that shows a need for the product.

## Design Search Typeahead - Case Study

1. MVP - Given few letters, show me X suggestion. 

a. Strict prefix of all suggestions. 
b. X can be 5. 
c. Most frequently searched terms. 
d. MVP means we do not focus on region wise search terms. 
e. How to add recency 
f. Minimum 3 letters for suggestions to show up.

Levenshtein distance - for typos

2. Estimation of scale

We have define read and write queries to determine the scale.

Read queries will be to return top 5 suggestions given some characters.

Write queries will be to write the entire search string that a user has used.

In this case, we might have 2x the number of reads to the number of writes. So this is both read and write heavy. 

Do we need sharding? This depends on what we store. We store all search terms and their frequency.

The number of searches that happen on google per day is appdroximately 10 billion. There could an existing term or a new term. In case of existing term we have to update the frequency of that term and in case of the new term, we have to create a new entry in the DB.

According to google, 25% of the search terms are new terms. This makes it 2.5 billion new terms every day. Each term has roughly 100 characters, so 100 bytes. This makes it 250 GB. If google stored this data every day for 10 years, then the total data would be 250 * 365 * 10. This comes to around 900 TB.

So we do need to shard the data.

3. Design goals

Should the system be highly available or highly consistent?

This system will be highly consistent when the frequency of the search terms are the same wherever they are stored. We dont really care about the exact frequency. We care about the trend.

What matters more is that when we type the search term in the search bar, google shows us the suggestions all of the time. This means the system should be highly availabe.

This system has to be low latency because we are competing with typing speed.

4. APIs

getSuggestions(search_prefix)
updateFrequency(search_phrase)

Data structures that can be used.

**HashMap**

We can have two hashmaps. One hashmap will have prefixes as keys and top 5 search term phrases and their frequencies as values. The other hashmap will have the search term and its frequency.

**Tries**

Tries is a tree structure, where the node at each level represents the character at the corresponding position in the phrase. If the search term is Michael Jackson, then the trie branch we would take would have 'm' as the first node, then 'i' as the child node to 'm', then 'c' as the child node to 'i' and so on. Each node can have multiple child nodes upto 26 characters. Of course, we are assuming that search terms will all be alphabets and will not have any other characters.

From the third node onwards, we will have, in each node, a list of top 5 pairs of search term and a pointer to its frequency, which will be at the node where the search term ends. We will also have a search term, if the search term ends at that node, and its frequency. When an entire search term is entered, we go to the end of the search term in the trie and then when returning to the root, we check at every node, if the search term is present in the top 5. If it is, we update the frequency. If it is not present, we check if the current search term's frequency is greater than any of the frequencies of the search terms in the list. If it is, we update the list to include the current search term and remove the one with least frequency.

**Storing these Data Structures**

There are hardly any databases that will be able to store the trie as it is. Either we will have to design our own database which can store a trie as it is in the disc.

The hashmap datastructure is friendly to shard but space required is more than Tries. As hash map keys could be in different machines, writes will be slower. 

How can we reduce volume of writes?

Writes are an intensive process because we have to take locks, access different machines where the data may be stored and hence will always compete with reads for resources. In a latency sensitive system, we want to minimize the number of writes to keep the read queries processing efficient.

There are two ways to reduce the volume of writes in a system.

1. Sampling - We randomly take an X% sample of all the search terms and update the frequencies of these samples. The sample is assumed to have the same distribution as the population of search terms. So we will capture the trend even if not the exact frequencies of all search terms. This is sufficient for our design goals which is highly available as opposed to highly consistent.

2. Threshold driven writes - We maintain a buffer hashmap with the search term as key and frequency as value. When frequency%1000 == 0, then we go and update the trie and we add +1000 instead of 1. The buffer hash map protects the tries from writes as large number of writes will slow down the system. So random search terms that have low frequency will not appear in the trie.

How should we shard the data stored in tries or hashmap?

In tries we can split by the first 3 terms.

In hashmap we can spit using consistent hashing applied on keys.

We can do random assignement of the shards to machines using consistent hashing or we can map the prefixes/keys to machines and allot the shards to the machines such that the popular search prefixes are spread out between machines.

**Adding Recency**

We want to emphasise popularity. Popularity is a combination of frequency and recency. There is a concept called time decay. We choose a time decay factor (TDF) and we adjust the frequency of the search term with this time decay factor. At the end of every day, we divide the frequency by the TDF. If TDF greater than 1, we will systematically decrease the weightage of past search frequency in the overall frequency number. This is done once a day for all the search phrases in the trie.

## How is data stored by NoSQL

In an RDBMS, every cell has a defined data type and space allocated. For example, if we have a column which has a datatype of varchar(20) (20 characters), and we have in a cell under the column a three character string, then we can update the string to 10 characters using inplace update easily.

How do we perform an update in case of a NoSQL key-value store saved in the disk? How do we store key-value data in the disk?

### Writes

The data that is store in the disk using NoSQL database system is immutable. This means, once created they cannot be changed. So, if we have to update, we have to create a new record with the updated value. 

For example, consider we have to store the prices of fruits and vegetables based on pincode. When we get a write request, we write the data into RAM. Once we hit a threshold of entries in the key-value store, which is in the RAM, we flush it to the hard disk. We flush it to HDD to persist, search and free up the RAM.

When we flush the data, we have to store the data in order. Searching through unordered data has to be linear which can be expensive when we have billions of records. So, we should sort the data and then flush it in that order as this makes search faster. If it is a hash map, we will sort by keys, if it is a column family, we will sort by row-key. For each key, we will allocate a certain block. The block size is Cassandra is typically 4 KB. If the size of value is greater than the size of 1 block, then we will need more blocks, the number of which will be stored as part of metadata. All of these blocks together is called sorted set 1. Writes will continue on RAM, and when we reach a threshold again, we will flush it to HDD to create a sorted set 2.

When we want to read latest data associated with a key, we first check the RAM because that has the lastest value. If not found, we go to SS 2 and if not found there, we go to SS 1. Time taken to search is directly proportional to one of the variables number of sorted sets. So to achieve faster reads, we can reduce the number of sorted sets. 

The number of sorted sets are reduced using async jobs that merge the sorted sets. This operation is called compaction. With the merged sorted sets, we have removed redundant values. Once merge operation is done, the older sorted sets are deleted and all the read requests will go to the new merged sorted set.

When should compaction happen?
1) Number of sorted sets have crossed a threshold.
2) When load on the system is less, check if compaction is required (time-interval).

### Reads

Now assume we have data in the RAM, SS1, SS2, SS3, SS4, SS5. If it takes 1 second to search in one sorted set, then we can take upto 5 seconds for a read operation. This is high latency, so we need to optimize our read operations.

We can make lookup tables for each sorted set. In the lookup table, we will store keys, startng block and ending block. Each row will be 24 bytes. The key will occupy 8 bytes and the two columns for blocks will hold data of datatype long. Assume we have 1 million entries in the lookup table. This meaans the lookup table will occupy 24 MB. If we have 10 million entries, the lookup table will occupy 240 MB. We dont want to store this in memory. We will store it in HDD.

Now, we will performa binary search on this lookup table to search for a key. To do this, we need the starting address of the sorted set, the number of entries, entry size. If we want to go to the middle point, we go to start + (number of entries * entry size)/2. We compare the key at the mid point and the key we are search. Based on this comparison we will either return the block or move to the left or right. We read the 24 bytes of data at the mid pointer in every binary search operation to do this.

Once we find the key, we have the address of the start block and the end block. We read the data of the value associated with the key and return it to the user.

We store the lookup table metadata in RAM. In this table, which we will call index table, we have the sorted set name, start address of the sorted set lookup table, number of entries and the entry size. When we want to perform the binary search operation on a sorted set lookup table, we get the relevant information from the index table.

### LSM trees

Lookup table is for sorted sets and index tables are for lookup tables. The number of sorted sets will never go to a 3 digit number. If we cann increase the number of entries in the index table and reduce the number of entries in the lookup table, then we can reduce latency. 

When reading data from the HDD, even though we want only 24 bytes, OS will read the whole block, which might 4 KB. This increase latency. To counter this, we can optimize the lookup table itself by decreasing the number of entries in it and increase the number of entries in the index table. This means increasing then number of sorted sets.

Suppose we have 10 million keys in RAM and it has hit our threshold limit. We have to flush the data to HDD. Earlier, we would create just 1 sorted set with all the keys and their associated values. But now, we decide to have only 1000 entries per sorted set. So we form a tree structure with root as range 0-10^7 with 10 children. Each of those children will have further 10 children. This will go on till we reach the lead nodes where each node is a range if 1000 values. How any leaf nodes are there? There are 10^7/10^3 = 10^4 leaf nodes. This is the number of sorted sets. 

The time it will take to reach the leaf node is (N/10^h) = 1000. So, h = log10(N/1000). Once we read the appropriate leaf node, we get the lookup table for the sorted set and do a binary search on the lookup table to get the key and its value. Now each lookup table will occupy only 24 bytes * 1000 entries = 24 KB. 

The main aim of LSM trees were to reduce the search space on the hard disk. We are not actually creating 10000 sorted sets. We are however creating 10000 lookup tables. The metadata of the lookup tables will be stored in the index tables. Using this metadata we perform the binary search in the lookup table. We arrive at the lookup table to use by traversing the LSM tree. The sorted set will still have 10^7 entries. So other steps like flushing the data in RAM to HDD is not impacted.

## Distributed Computation

How do we do computation in different machines and merge it? Let us take the example of del.icio.us, we shard the data of each user based on user id. Suppose we want to find the number of users who have bookmarked a particular website. 

Here we introduce the concept of MapReduce. The three steps here are map, shuffling and reduce. 

The map step takes a string as input and it gives 0 or more key-value pairs. The reduce takes key and list of values and will also return key-value pairs. 

MapReduce takes an input and divides it to multiple machines, executes some code, output is combined and returned as though the operation was performed on a single machine.

For this example, the map function runs on ultiple machine and returns the bookmarked wesbite as key and the number of times it appears in the list of bookmarks of every user and returns it as value. 

The shuffle then allocates a single machine for every key. Here we can use key%number of machines or even consistent hashing to allocate to machines. 

The reduce function, which is running on each machine will then receive inputs of key and list of values. So, for example the machine allocated for yahoo.com gets key as yahoo.com and list of values as [1], the machine allocated for google.com gets key as google.com and list of values as [1, 1]. In reduce function, we will return the sum of values in the list for each key and returns it.

The way to think about the application of MapReduce is to think about the final form of data that we want and how to achieve that in the reduce step.

All these steps are running on multiple machines. 

Consider another example in which we have deer, cat and bear in 1 machine and dog, cat and deer in another machine and bear, dog and bear in another machine. We want the word count, so the final output should be
```
deer ---> 2
cat ---> 2
bear ---> 3
dog ---> 2
```
The map function, which runs on every machine will return deer:1, cat:1 and bear:1 from the first machine, dog:1, cat:1 and deer:1 from the second machine and bear:2 and dog:1 from the third machine.

The shuffle function, which is also running on multiple machines, will assign each key to a machine.
The reduce function, which is running on multiple machines, will receive the key and list of values and perform the sum operation and return the word - count as key - value pair, which is the output that we want.

Another example is a friend list. In machine 1, a has b,c,d as friends, f has c as friend. In machine 2, b has a, c, e as friends and e has b as friend. In machine 3, c has a, b, f as friends and d has f, g as friends. Return mutual friends for all pairs. From machine 1 we make the map function return ab --> (b, c, d), ac --> (b, c, d), ad --> (b, c, d), fc --> c. From machine 2 we make the map function return ba --> (a, c, e), bc --> (a, c, e), be --> (a, c, e). From machine 3, we make the map function return ca --> (a, b, f), cb --> (a, b, f) and cf --> (a, b, f), df --> (f, g), dg --> (f, g). Then, in shuffling, we assign key pair key to each machine for the reduce operation. In the first machines, 

## Zookeeper + Kafka

- Reliability
- Why do we need Kafka?
- What is Apache Kafka?
- Cluster, Broker, Core of Kafka
- Producer & Consumer
- Demo
- Producer and Consumer
- Assignment - (Use lambda, SQS)

### Reliability

If your system is able to perform correctly inspite of adverse event.

eg pass funny long string to google search. Should reply with a reasonable message aboout not being able to process instead of system down

### Linkedin Story

Linkedin. Rapid growth from 2009. System not able to cope with all the moving parts.

DB, Data warehouse clusters, SQLDB, applications, payment service etc. A mesh of the components. Network choking due to these interconnected components.

Kafka built by Linkedin. Open sourced in 2012. 

Producers produce the messages. Consumers consume the messages. Broker (Kafka) stores the messages.

Consider Amazon. There is a producer which producers order placed messages. Consumer 1 is notifier that notifies customer. Consumer 2 is a shipping service. Consumer 3 is a fraud detection system. 

Producers produce events/messages. Consumers consume them. It follows the pubsub model.

Broker takes data from producers and gives them to consumers. 

### Linkedin Design Goals

1. Message broker system which can have high throughput. Million messages per second should reach consumers.

2. Scale horizontally. There should not be any limit to add machines.

3. Producers and consumers should not be coupled. 

4. Fault tolerant. Any component goes down, whole system should not go down.

### Topics

Producer is producing messages on a specific topic. Consumers subscribe to the same topic.

Scaler classroom. instructor procducer. Students consumer.

Kafka storing all the messages as topics. Each topic can have multiple messages.

There is a fast producer and slow producer. Some consumers may be fast, some may be slow. Kafka provides message retention. Consumer needs to specify the offset. It means, i have read till message 3, give me the next message. Producer will say I have produced till message 5, here is message 6. Offset is the message number. 

Message retention is configurable. 7 days is default (168 hours).

Suppose message in a topic takes the form
```
{
   OrderId:________,
   CustId:________,
   timestamp:_______,
   Address:_______,
   emailId:_______,
}
```
We have to implement serializable interface at the producer end. Coonsumers will have to deserialize.

How do we make this system fault tolerant?

Broker store messages of topic. It is storing it in a log format. We should have replicas of a broker. All the replicas are in sync which means all the brokers will have the same log file. There is a leader and followers. If a leader fails, a follower will then become a leader. If a follower goes down, Kafka will get another machine to become follower. 

We can define the success response for a producer by setting a) Leader got the message b) Leader and 1 follower got the message c) Leader and all followers got the message.

Zookeeper manages leader and follower management. 

## Zookeeper + Kafka 2

### Zookeeper

Consider the master-slave architecture of a DB system. When a write comes, it has to come to the master in a master-slave. This means all systems should be aware of who the master is. If the master dies and a new machine becomes the master, all other systems should know about this change. 

One solution is to keep track of the master at a single source. This single source does not need to be a single machine, but can be a cluster of machines. Other parts of the system can talk to the cluster to find the master.

Another problem statement is that the single source cluster have to keep track of the health of the master. 

So, the cluster has two jobs.

1. Track health of master.
2. Inform appServers and slaves of who the master is.

In case of a cluster of machines, do all of them keep track of the health of the master independently? How do we ensure all the machines in the cluster have the same information about the health of the master.

Zookeeper, which is what the cluster is called, has directories and files in one system. It will have a file named master in the root. Every file in Zookeeper can be ephemeral or persistent.

Let us look at the case where files are ephemeral. Consider a bunch machines (M1, M2, M3, M4) in which one can be the master and the other slaves. If the master file in Zookeeper is NULL, then all the machines can attempt to become the master by writing its IP address in the master file. Whichever machine writes it IP first in the master file becomes the master. The machine that becomes the master has to periodically (every 5 seconds) inform the Zookeeper about its status. In case the Zookeeper does not hear from the current master for the last 5 seconds, the content of the master file is removed. 

All the other slaves and appServers are subscribed to the Zookeeper node, which in this case is the file named master. When there is a change in the master file, Zookeeper will send an event to all the subscribers. In this case, all the slaves will again try to become the master and will try to write its IP address in the master file. Whichever machine writes its IP first, that machine becomes the new master. All the subscribers are once again sent an event of the change in the master file. Now all the parts of the system know which machine the new master is.

A function in the slave could look like
```
def zkNodeDataChanged(zk_node, new_data):
        if zk_node == "master" and new_data is NULL:
                try:
                        zk_client.write("/master", own_ip)
                        master = True
                except:
                        master = zk_client.read("/master")
```

We can also have persistent nodes. The file does not change. This is useful for configuration files.

Which machine in the cluster is responsible for carrying out the operations described above?

Assume there are 5 machines in the cluster (Z1, Z2, Z3, Z4, Z5). Zookeepers try to reach a quorum when there is a read or write request for the zookeeper. If there are x machines, then majority is (x/2) + 1 and majority is quorum. Zookeepers also elect a leader. When a write request comes to the leader, then the leader propogates the write request to the other machines in the cluster. Once a quorum is achieved, only then the leader return success. If a quorum was not achieved, then we return failure and all changes made will be rolled back. The same is the case with read requests. Unless a quorum of machines return the same data, the leader cannot send a response to the read request.

Why do we need majority as quorum to return success? Suppose there are 5 machines and we have set quorum as 2 machines. Some network failure happens and two machines are partitioned off from the other three machines. When the leader gets a write request, it writes to one another machine and achieves the quorum. Assume this was in the group of 2. Another machine in the other group also gets a write request for the ip address of another machine and that also achieves quorum. So now for every read request, the response can be any of the two machines when it is only supposed to be one master. This will not happen when we set the quorum to be majority. The phenomenon here is called split brain.

Reading from quorum is important in the event that the current leader dies and a new leader with possibly inconsistent value is elected.

Zookeeper provides a client library. We can initialize the zookeeper with a name for the zookeeper. The client will then let us read(), write(), create() (a directory) or subscribe(). 

### Persistent Queue

Imagine Kamal has sent Wasim a message 'Hi'. Once the message is received by the server and stored in the Wasim's db, then a bunch of things have to be done. We need to notify Wasim, send an email to Wasim if Wasim's messages have not been checked for 24 hours, send some data to analytics, update some sort of score that measures the users' closeness with each other. 

We dont want to return message sent/success after all the tasks are complete because that might take some time. We want to return success as soon as the message is written to the DB.

Here, there are a bunch of tasks that have to be done asynchronously and reliably. This is where we have to use something called persistent queue. Persistent means we are writing on the disk. The queue is durable. We publish the event onto the queue. All the services that are responsible for the tasks, subscribe to the queue and read the event from the queue at their own pace.

In a queue we can have different kinds of events. Some services may subscribe to the queue for some events and other other services may subscribe for other events. So we can segregate events into different categories in the queue. These categories are called topics.

For example, in Flipkart, we can buy a product or message vendor. When a user buys a product, Flipkart will notify the warehouse, send an invoice, send an email, send data to analytics etc. When a message is sent to vendor, we may want to email the vendor, call the vendor when there is no reply, update analytics on reputation of a vendor based on the content of the message.

If we public both these kinds of events in the queue, irrelevant events will be consumed by the services. We can classify the events as topic. Buying a product is topic 1 and sending a message to a vendor is topic 2. Invoice generation service subscribes to only topic 1.

A persistent queue example is Kafka. 

Kafka supports about 1 million events per second as throughput.

Persistent queue is different from a database. This means we dont want to store the events forever. Usually, queues have a message retention period. By default retention period is 1 week. When we add events, we add at the end. We read events from the front. The entries made are immutable. We cannot change an entry that has been made. 

Topics can also become very large. We do not want a topic to be in a single machine. We want to break it down into multiple parts so that a single machine does not become a bottleneck. Kafka allows us to specify the number of partitions per topic.

Partitions mean more storage as we are not limited by a single machine. Patitions also allow us to parallelize consumption.

Imagine we have a set of producers who publish events. There are a bunch of consumers who consume events from the queue. The machines inside Kafka are known as brokers/servers. As long as we know about 1 broker/server our requirements are satisfied because the broker will ensure that the request reaches the correct machine inside the Kafka cluster. So producers have to pick 1 broker ip, topic, event_message and a key if we want. If key is Null, which is the default, all the requests are split between partitions in a round robin manner. If we specify a key, then request goes to a specific partition. The partition assigned key is determined using hash(key)%num_of_partitions.

Consumers will talk to a broker_ip and will want events related to a particular topic. They will also maintain an offset which is the index till which consumers have consumed the events in the topic. They have to maintain partition wise offsets. 

Within a partition, we can determine the sequence of events. However, across partitions we cannot determine the order of events. 

There is usually a consumer group (C1, C2, C3). Each topic can be divided into partitions and these topic-partition pairs are distributed amongst multiple servers. Assume we have 3 topics and each topic is divided among 3 partitions. So the pairs are T1P1, T1P2, T1P3, T2P1 T2P2, T2P3, T3P1, T3P2, T3P3. These pairs are divided among the servers. If we have fewer severs, some of them will be assigned two partitions of the same topic. More the servers, more the likelihood that each partition of a topic gets assigned to different servers. The advantage of this is that any particular service can be parallelized. 

Suppose the generateInvoice service is running on a cluster of machines, say 3. Each of these machines can subscribe to a different partition of the topic concerned. This way the service is parallelized and the speed of the service has now become 3x. 


## Messenger Case Study

Through this case study we will learn about idempotency and heartbeat.

**Design of a Messaging Application**

Types of messaging apps:

1. Whatsapp ==> 1:1 chats (No storage).
2. FB Messenger/Telegram ==> 1:1 and group chats (Storage).
3. Slack/MS Teams/Discord ==> group chats (Storage).

**MVP Requirements**

*Ability of someone to chat with others*
*Online indicator* - Application of heartbeat.
*Read/delivered/sent indicator* - Similar to online indicator.
*Only text vs multimedia* - Text messages will have limit of 10000 characters per message.
*Group messages* - Not focussing on this. 
*See recent chat history*
*See past messages*
*Notifications*
*Authentication* - Not focussing on this.

**Estimation of Scale**

Is our system read intensive or write intensive? In group chat, the system will be read intensive. However, in individual chats, every message is likely to be read on average twice. So the system will be both write and read intensive.

Why is estimating number of reads vs write important?

1. The answer to this helps us decide which kind of DB to use.
2. No DB in the world can handle large number of writes as well as large number of reads.

If there are large number of writes, we can go to Cassandra or HBase. If there are large number of reads, we can go for SQL etc.

If there are equal number of reads and writes, we cannot go for SQL because it is not optimized for quick writes. If any database is optimized for reads, then we cannot used them efficiently for writes. In the case of equal number of reads and writes, we will use a database which is optimized for writes along with some optimizations that make reads faster. For example, using cache to make the reads faster. 

The only difference between an SQL and a NoSQL database is that we have done sharding in the NoSQL database. To optimize the reads, be it SQL or NoSQL, we need extra information otherwise it becomes an O(N) search operation. The creation and maintenance of this extra information is done during writes, which makes writes an expensive operation. Updating information in the disk and then updating the index makes the writes slower. 

So this system has equal number of reads and writes.

We need to find the size of data that we need to store. Depending on the size of data, we need to determine if a single machine is sufficient to store the data or if we need to shard the data to multiple machines. 

A messenger store messages. Every message will have senderID, recepientID, timestamp, text, messageID. All the attributes of a message other than text will be 8 B in size as they are all long integer. If we allow emojies etc, then the text will be stored as unicode characters. Each unicode character occupies 4 B. The max size of text will be 40000 B. If we assume average text size to be 280 characters, then this translated to about 250 * 4 B = 1KB. So, one message will occupy approximately 1 KB in size.

How many messages will be sent per day? On whatsapp, for example, about 50 billion messages are sent everyday. This translates to 50 * 10^9 * 1000 bytes = 50TB. So, we cannot fit the data in a single machine. We will need to shard.

If we store all the messages per day, then we can estimate about 50 * 365 * 5 = 90000 TB = 90 PB of storage in 5 years.

For data to fit in one machine for 1 year, the data will need to be in 2 digit GB. 

For QPS, assume 1:3 differential between regular and peak hours in case of messenger apps. In case of stock trading applications, assume 1:10 regular to peak hours QPS ratio.

**Design Goals (Non functional requirments)**

System should have low latency and high throughput. Low latency means sending one message should take less time. High throughput means high number of messages can be sent per unit time.

We also want a consistent and highly available system. This is the design goal set by facebook for their messenger app.

**API Design**

The first api is,
```
sendMessage(senderID, receiverID, text)
```
If this is the function signature, then there is a potential problem. When we send a message, this function is called and the data is sent to the server. Suppose we sent two messages, 'Hi' and 'How are you?' one after the other. The transfer of first message from client to server may fail but the transfer of second message may succeed. The second attempt at transfer of the first message may succeed. If this happens, then the server will receive the second message first and then the first message. The server needs to know the order of messages sent so that it can send the messages to the receiver in the correct order. 

Another issue that can come up is, when a message is sent by the client and received by the server, an acknowledgement is sent back to the client. If the acknowledgement fails to reach the client due to network failure, the client could resend the same message to the server. This means the server will have two messages of the same kind and may deliver both to the receiver. This is undesirable.

We need a way for the server to drop duplicate messages. Can we do this based on the text of the message that we sent? No, because users may send identical text messages one after the other, for whatever reason, all should be treated as distint messages. 

Here we introduce the concept of idempotency. When we click on the send button in our messenger app, we do not want the message to be sent twice. Another example is when we click on the pay button on Amazon, we do not want the payment to deducted twice.

To solve both the issues outlined above, we use idempotency key. When we click on the send button an idempotency key is generated for the message. This key will help to prevent duplication and redundancy. In the sendMessage function, we will send the idempotency key. If the server receives a message with an idempotency key it has already received, then it discards the second one.
```
sendMessage(senderID, receiverID, text, idempotency_key)
```
If we are able to ensure idempotency keys of different messages in 1 conversation are in order, then we can ensure the correct order of messages while deivering them to the receiver. This means the client has to maintain an order in the idempotency_key. If the client maintains a count of the number of messages in a conversation, then that can serve as the idempotency key.

The second api is
```
getRecentConversations(user_id, limit, offset)
```
When open the messenger app, we want to see the recent conversations. However, we do not want to load all the conversations of a user. So we can apply pagination by specifying a limit and offset. If we make limit = 10 and offset = 1, the api will return the first 10 conversations. If limit = 10 and offset = 11, then we get the next 10 conversations and so on.

The third api is 
```
getMessages(sender_id, receiver_id, limit, offset)
```

**Architecture**

There is always a server in between the sender and receiver. There are two ways to build a messaging app. 

1. Peer-to-peer - Here, the server has the job of telling the sender the IP address of the receiver.
2. Client-server

In storage, we have to store messages. As we are going to shard the data, we have to choose a sharding key. In this case, we have couple of options to choose from. These are user_id and conversation_id.

Let us look at the impact of each choice on the number of shards we will have to access to perform an operation.

If we choose conversation_id as the shard key, then each machine will have different conversations stored as shards. Given this, let us look at how the APIs perform their operations and the number of shards it would need to access.

For sendMessage 1 shard will be updated.
For getMessages 1 shard will be accessed to get the messages of a conversation.
For getRecentConversations every shard will be accessed because all the shards may contains conversations of a user.

If we choose user_id as the shard key, then each machine will have all the data of a user stored as shards. Given this, let us look at how the APIs perform their operations and the number of shards it would need to access.

For sendMessage a maximum of 2 shards will need to be updated. One machine will have the data of sender and another machine will have the data of receiver.
For getMessages 1 shard will be accessed. We can access any one of the sender or receivers messages to get messages of a conversation.
For getRecentConversations 1 shard will be accessed which is the shard which has the user's data.

Given the difference in impact on operations, user_id is the appropriate choice as the shard key.

The only time user_id as shard key leads to a worse outcome compared to conversation_id as shard key is when we want to sendMessage. The problem statement here is that we have to store data in two shards. One thing that could go wrong here is that writing to the shard that has the receiver may fail. This means the sender receives acknowledgement that the message has been sent, but the receiver does not receive the message.

First solution is to send acknowledgement to sender only when writes are complete on both shards. However, this affects latency.

Second solution is to write to the shard that contains the receiver. If the write fails return faiure to sender. If the write succeeds, then proceed to write onto the shard that contains the sender. If this is a success, then we can return success to the sender. If it is not a success, we can stil return success to the sender because the receiver will receive the message. So irrespective of the result here, we can return success to the sender if the write to the receiver is successful. Since there is write to only 1 server before sending success back to the sender, the sender does not experience increased latency.

Sharding key - User id vs Conversation id. Choose user_id.

We have to write on two servers. Write on receiver first.

Load balancer ---> AppServers ---> DB.

System will have equal number of reads and writes. 

If we have to read fast, we have to write to multiple places and vice versa. When we have a system that is 1:1 read to write ratio, we have to choose a database that is optimized for read or write and choose another database that is optimized for the other. We keep both in sync as per requirements. If requirement is highly available, we can sync after sometime, which means eventual consistency.

### Database for writes.

Normally SQL databases are bad for writes because of ACID and index updation. We will use HBASE which is a NoSQL database.

HBase can handle large number of writes easily. However reads are slow. 

On HBase, write is just an append on a commit/transaction log. Storing the data and other steps happen later asynchronously. To read the current value of a column, we have to go through the entire transaction log. This means for older data, reads will be faster than for newer data. MongoDB updates the disc in a write transaction.

For reads, we use in-memory cache.

We have to sync between the cache and disc.

There are three types of cache. write-through, write-back and write-around cache. Choice depends on consistency vs availability. 

Before a write is completed, we have to ensure data is written on HBase because cache can crash and we could lose the data if only written on cache.

Write back is ruled out.

In write around, we update DB and DB asynchronously updates cache. When a message is sent, most people will read message immediately after it is sent. We need to ensure message is there is the cache. So, write around is not a good choice.

In write through, we will write to both DB and cache and return success only after both return success.

Client sends a message ---> Load Balancer ---> AppServers ---> Written on HBase ---> Written on Cache ---> Return success.
```
sendMessage(from, to, text) {
        writeToHbase();
        writeToCache();
        if (both success) {
                return Success;
        }
        return Fail;
}
```
Both the writes happen in parallel.

We generally read older messages infrequently. Can have fall back with data in SQL.

### Sending Messages

How will client talk to server?

In HTTP1, a server cannot initiate a connection with the client. A client has to initiate connection with the server and the server responds.

There are three ways to do this.

1. Polling - Client repeatedly asking server if there is a message for them.
```
Client {
        while (True) {
                checkServerForNewMessage()
                sleep(10)
        }
}
```
This is resource intensive because the client is sending a new request, creating a TCP connection, doing the TCP handshake and then the client gets the data.

If 1 billion users are sending requests every 10 seconds, too many requests for server.

Out of 8640 intervals of 10 seconds per day, we probably get about 100 messages per day, which means we get a positive response from server for only about 100 intervals out of 8640. So checking for new messages every 10 seconds is a waste.

In a realtime chat, we get messages after 10 seconds. This is not ideal.

2. Long Polling

There is a client and there is a server. Client sends a getNewMessage() request. Server is not obligated to reply to it immediately. Server will respond only when it has a new message.

This is not as resource intensive as polling. The TCP connection will always be maintained. Every http request creates new TCP connection. So the number of new connections are reduced. However, on the server side, the number of open state TCP connections are restricted. It eats memory. This is a problem even with websockets. Solution for this is to have multiple servers where the connections are distributed across the machines. 

There is a timeout in every HTTP request. In case of a timeout, client will send a getNewMessage() request again.

The number of requests are reduced to mostly 1 request per message. This is an improvement over the polling method.

The problems with long polling are, 

1. New TCP connection has to be established on every request. We still need to do a 3 way handshake for every request which is a waste of resources. An ideal solution is to maintain a single connection between client and server that can be used whenever desired. We can use this when we have to send messages between them. 

3. WebSockets

When a client comes online, a cnnection is setup between client and server. This connection remains open till the time user is connected to the internet. This connection can be used by server to send new message/notifications etc. This connection can be used by the client as well.

Websocket is a protocol that works over HTTP and TCP where a connection is established between a client aad server and connection is persisted that allows clients and servers to talk to each other whenever needed.

Scaling websockets is hard.

1. Learn how websockets work
2. How to create a websocket connection
3. Chat applicaton using socket.io

Multiple Clients maintain a connection with load balancer. Load balancer assigns each connection to appServers. There will not be a single load balancer. There will be geo dns that estabish the client connection to the load balancer that is closest to the client. AppServers talk to each other using a messaging queue like Kafka. Every server subscribes to Kafka for messages of users that have established connection to the server. Suppose there are 2 servers. Users A, B and C have established connected to server 1. Users D, E and F have established connection to server 2. Server 1 will subscribe to Kafka for A, B and C and tells Kafka to send any event for A, B and C to server 1. Server 2 will do the same for users D, E and F.

Whenever any new message is sent, after storing the message in redis and hbase, an event is sent to Kafka. 

What happens when the receiver is offline and they do not have an open connection with the server. When the user joins/comes online, they will first establish a connection, then send an http request getUndeliveredMessages() and this will be served by cache or HBase. Now, we will be in sync.

Even though undelivered messages will be stored in Kafka, as the server will not have subscribed to receive events for the user, the messages will not be delivered unless we flush them from the topics in Kafka, which is a slow process. The getUndeliveredMessages method is used more often.


### Notifications

In the current architecture, we have handled message sent notification through Kafka sending the message to the appropriate server and the server sending the message to the receiver. 

However, there are other notifications like app is not working (system down) etc.

In mobiles, we dont send notifications directly via websockets. For android, we have to use firebase cloud messaging. For iOS, we have apple push notification. 

Let us say we want to send a notification to a user like the websocket is not working or they are not connected to the internet. We can use a notification service to send any kind of push notification to the users. For a notification service, we will need the messages, who to send the notification to, where to send the notification to. We can have an internal service called notification service. This notification service is an independent service that can be called by anyone. If we have to send a notification in the system, we will send it via this system. A notification service will need to know about the device it has to send the notification to. Where can we store the device id? We will need to store for every user the type of devices they have. This will remain somewhat constant.

When notification service receives a request, do we have to immediately send the notification? No, because we may need to do rate limiting etc. Notification service will push the notification to a queue. Notification service is usually configured to be a best-effort service. Notifications are good to have but they are not must haves. If notifications go missing, then that is okay. There are workers in the system who reads these messages in the queue and they call firebase cloud messenger or apple push notification or email service etc. These workers are connected to a datasource that has the information on the device associated with a user. 

### Online Indicator

What does being online mean?

1. If there is a websocket connection between client and server. 
2. If the app is open. 
3. If you are interacting with the app.

Here we choose to indicate online when the app is open.

There is no need to 100% accuracy. Even almost accurate is fine.

This is where we use heartbeat mechanism. This will be implemented by the a service called online indicator. As soon as we open the application, we can send a heartbeat every 10 seconds to the server telling the server that we are online. We should not send an http request for heartbeat. Like API requests in HTTP, there are websocket messages. When the app is open, we can send a ping to the server. Server can store something like user_id and status. Another option is server can store user_id and timestamp. Whatsapp follows the second option, but facebook messenger, microsoft teams etc follow the first approach. 

If following first option, we can show online/offline, but we cannot show last seen at timestamp. If we store user_id and timestamp, this data will change every 10 seconds. It will also be read every 10 seconds. So we have a large number of reads and writes. One way to make writes and reads fast is to use cache. Cache can crash, so we need to persist this data. We can, along with cache, also use SQL DB to store. However, the writes to SQL DB will take time. To reduce the latency here, we can store bulk writes at regular intervals. This design is supported by write-back cache. This is okay, as we do not need high consistency here. 







