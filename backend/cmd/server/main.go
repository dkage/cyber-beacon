package main

import (
	"net/http"
	"os"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/joho/godotenv"
	"github.com/rs/zerolog/log"
)

func main() {
	setupLogger()

	if err := godotenv.Load(); err != nil {
		log.Fatal().Err(err).Msg("error loading .env file")
	}

	port := os.Getenv("APP_PORT")

	router := chi.NewRouter()
	router.Use(middleware.Logger)

	router.Get("/", func(w http.ResponseWriter, r *http.Request) {
		if _, err := w.Write([]byte("Hello, world!")); err != nil {
			log.Error().Err(err).Msg("failed to write response")
		}
	})

	log.Info().Str("port", port).Msg("API Server starting")
	if os.Getenv("APP_ENV") == "development" {
		log.Info().Msg("running in development mode - http://localhost:" + port)
	}

	if err := http.ListenAndServe(":"+port, router); err != nil {
		log.Fatal().Err(err).Msg("server failed")
	}
}
