from fastapi import FastAPI
# from mutualFundApp.urls import mutualFundApp
from website.urls import website
# from depositsApp.urls import depositeApp
from mangum import Mangum

app = FastAPI()

# app.include_router(mutualFundApp)
app.include_router(website)
# app.include_router(depositeApp)

handler = Mangum(app)