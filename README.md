https://dev.splitwise.com/#section/Introduction

https://github.com/namaggarwal/splitwise

git submodule init/update, set up secrets, poetry init, poetry run python3.9 -i app.py, mkexpense()

roadmap:

- technillogue.xyz (or register earnest.xyz?) http endpoints for registering a split and making an expense with a split
- mobile-friendly webpage form for the above
- script to push to technillogue.xyz
- secrets managed as environment variables for easiest security

eventually, maybe:
- slack #receipts integration
- google sheets split calculation integration
- push income changes from slack

```
gcloud init # (login, choose the region, choose the earnest project, etc)
set project (gcloud config get-value project)
gcloud builds submit --tag gcr.io/$project/earnest 
gcloud run deploy --tag gcr.io/earnest-314020/earnest --platform managed
```

running into poetry not finding gunicorn
