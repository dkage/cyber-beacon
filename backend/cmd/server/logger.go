package main

import (
	"io"
	"os"

	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
	"gopkg.in/natefinch/lumberjack.v2"
)

func setupLogger() {
	logFile := &lumberjack.Logger{
		Filename:   "./logs/app.log",
		MaxSize:    10,
		MaxBackups: 5,
		MaxAge:     30,
		Compress:   true,
	}

	multi := io.MultiWriter(zerolog.ConsoleWriter{Out: os.Stderr}, logFile)
	log.Logger = zerolog.New(multi).With().Timestamp().Caller().Logger()
}