{-# LANGUAGE OverloadedStrings #-}
module Main where

import Web.Scotty
import Network.Wai.Middleware.RequestLogger (logStdoutDev)
import Data.Aeson (object, (.=))
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.Lazy as TL
import qualified Data.Text.Lazy.Encoding as TLE
import System.Environment (lookupEnv)

lev :: Text -> Text -> Int
lev s t = d (T.length s) (T.length t)
  where
    d i j
      | i == 0 = j
      | j == 0 = i
      | otherwise = minimum [ d (i-1) j + 1
                            , d i (j-1) + 1
                            , d (i-1) (j-1) + cost ]
      where cost = if T.index s (i-1) == T.index t (j-1) then 0 else 1

main :: IO ()
main = do
  host <- maybe "0.0.0.0" id <$> lookupEnv "HASKELL_TOOLS_HOST"
  port <- maybe 8089 read <$> lookupEnv "HASKELL_TOOLS_PORT"
  scottyOptsT (Options 1 (read $ show port)) id $ do
    middleware logStdoutDev
    get "/health" $ json (object ["ok" .= True])
    post "/levenshtein" $ do
      bodyBytes <- body
      let txt = TL.toStrict (TLE.decodeUtf8 bodyBytes)
          parts = T.splitOn ";" txt
      case parts of
        (a:b:_) -> json (object ["ok" .= True, "distance" .= lev a b])
        _       -> json (object ["ok" .= False, "message" .= ("expected 'a;b' in body" :: Text)])
