#!/usr/bin/env python

"""
tweets.py
=========

Implement a cached tweet database with all the rate limiting
and message filtering.

Usage
-----
python tweets.py "@engadget" 

History
-------
:2010-07-07: Initial coding without filtering implemented.
:2010-07-08: Implemented queue (pop/pending) interface

Todo
----
* Non-blocking updating
* Explicit message filtering
* Use twitter streaming API

"""

__author__ = 'David F. Gleich'
__license__ = 'BSD'

import sys
import time
import urllib
import operator

import twython.core as twython

import text_censor

# get a twitter object
twitter = twython.setup()

class TweetStream:
    """
    A TweetStream is a stream of twitter messages in response
    to a search.  This code implements a nice queue view of this
    stream.
    
    s = TweetStream(["#lastfm"])
    while 1:
        while s.pending():
            print s.pop()["text"]
        time.sleep(20)
        
    In can also be used in batch mode.    
    while 1:
        if s.check_for_new_tweets():
            ts = s.tweets(new_tweets=True)
            for t in ts:
                print t["text"]
        time.sleep(20)
    
    """        
    def __init__(self,terms,rate=150,filtered=True,max_history=None,
        keep_initial=True):
        """
        @param terms the list of search terms
        @param rate the rate of requests per hour
        @param filtered whether or not to filter messages for
          inappropriate messages
        @param max_history an option to limit the length
          of the history cache, by default this code saves 
          every single tweet it collects
        """
        self.terms = terms
        self.rate = rate
        self.filtered = filtered
        self.query = " ".join(terms)
        self.max_history = max_history
        
        if filtered:
            self.censor = text_censor.ShortTextCensor()
        
        self.last_status_id = 0
        self.last_query = 0
        self.cache = []
        self.queue_position = 0
        self.new_results = 0
        self._update_cache()
        
        self.censor = text_censor.ShortTextCensor()
        
    def _update_cache(self):
        # check that we haven't exceeded the rate
        curtime = time.time()
        if curtime - self.last_query < 3600/self.rate:
            #print "TweetStream:_update_cache skipped due to rate limit"
            return
        # stupid initialization code
        if self.last_status_id is 0:
            rval = twitter.searchTwitter(self.query)
        else:
            rval = twitter.searchTwitter(self.query,
                            since_id=self.last_status_id)
        self.last_query = time.time()
        
        if 'results' in rval:
            results = rval['results']
            # sort results by id
            results = sorted(results,key=operator.itemgetter('id'))
        else:
            #print "TweetStream:_update_cache did not receive results"
            results = []
            
        for r in results:
            # these are sorted now
            if r['id'] > self.last_status_id:
                # this post is feasible
                if self.filtered:
                    # check if it passes the filter
                    if self.censor.check(r['text']) is False:
                        self.cache.insert(0,r)
                        self.new_results += 1
                        self.queue_position += 1
                    else:
                        print "TweetStream:_update_cache filtered %s: %s\n"%(
                            r['from_user'], r['text'])
                        
                        
        
            
        if 'max_id' in rval:
            self.last_status_id = max(self.last_status_id,rval['max_id'])
            #print "TweetStream:_update_cache set last_status_id=%i"%(
            #        self.last_status_id)
        else:
            if len(results) > 0:
                max_id = 0
                for r in results:
                    max_id = max(max_id,r['id'])
                self.last_status_id = max(self.last_status_id,max_id)
                #print "TweetStream:_update_cache computed last_status_id=%i"%(
                #    self.last_status_id)
                    
        # check history truncation
        if self.max_history is not None and len(self.cache)>self.max_history:
            self.cache = self.cache[0:self.max_history]
            self.new_results = min(self.new_results,self.max_history)
            if self.queue_position > len(self.cache):
                self.queue_position = len(self.cache)
        
        
    def tweets(self,new_only=False):
        """ Get the full database of tweets, including unpopped ones """
        
        new_results = self.new_results
        self.new_results = 0
        if new_only:
            if new_results > 0:
                return self.cache[0:new_results]
            else:
                return []
        else:
            return self.cache
            
    def pop(self):
        """ Access the next tweet in the stream """
        if self.queue_position > 0:
            self.queue_position -= 1
            assert(self.queue_position < len(self.cache))
            return self.cache[self.queue_position]
        else:
            return None
            
    def tail(self):
        """ Access tweets that have already been popped """
        return self.cache[self.queue_position:]
    
    def pending(self,update=True):
        """ Return true if there are unpopped tweets """
        
        if self.queue_position > 0 and len(self.cache) > 0:
            return True
        else:
            if update:
                self._update_cache()
                return self.pending(update=False)
            return False
        
    def check_for_new_tweets(self):
        self._update_cache()
        if self.new_results > 0:
            return True
        else:
            return False
            
def main():
    terms = sys.argv[1:]
    print "Searching for \"" + "\", ".join(terms) + "\""
    print "-------------"
    print 
    s = TweetStream(terms)
    while 1:
        if s.check_for_new_tweets():
            print "Found %i new results"%(s.new_results)
            ts = s.tweets(new_only=True)
            print "Got %i tweets"%(len(ts))
            for t in reversed(ts):
                print t['from_user'] + ": " + t['text']
        time.sleep(30)
        
    

if __name__=='__main__':
    s = TweetStream(["#lastfm"])
    while 1:
        while s.pending():
            print s.pop()["text"]
        time.sleep(20)


