# NC-CommonSensing

A solution to Winograd Schema Challenge with narrative chains.

To run the sample questions, we assume you have java and python pip installed, then please execute the following script. A Stanford CoreNLP package (~400M) will be downloaded.

```bash
$ git clone https://github.com/samsdolphin/NC-CommonSensing.git
$ cd NC-CommonSensing
$ sh setup_environment.sh
$ java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer
$ python solve_wsc.py
```

- Reference: Altaf Rahman and Vincent Ng. 2012. Resolving Complex Cases of Definite Pronouns: The Winograd Schema 
Challenge.  In  Proceedings  of  the  2012  Joint  Conference  on  Empirical  Methods  in  Natural  Language 
Processing and Computational Natural Language Learning, page 777-789. 
