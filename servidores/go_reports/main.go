package main

import (
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/jung-kurt/gofpdf"
)

func health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"success": true, "service": "go-reports"})
}

func rncPDF(c *gin.Context) {
	id := c.Param("id")
	pdf := gofpdf.New("P", "mm", "A4", "")
	pdf.AddPage()
	pdf.SetFont("Arial", "B", 16)
	pdf.Cell(40, 10, "Relatório RNC IPPEL")
	pdf.Ln(12)
	pdf.SetFont("Arial", "", 12)
	pdf.Cell(40, 10, "RNC ID: "+id)
	// TODO: fetch details from Python API if needed

	c.Header("Content-Type", "application/pdf")
	c.Header("Cache-Control", "no-store")
	err := pdf.Output(c.Writer)
	if err != nil {
		c.Status(http.StatusInternalServerError)
	}
}

func main() {
	gin.SetMode(gin.ReleaseMode)
	r := gin.New()
	r.Use(gin.Recovery())
	r.GET("/health", health)
	r.GET("/reports/rnc/:id.pdf", rncPDF)

	addr := os.Getenv("GO_REPORTS_ADDR")
	if addr == "" { addr = ":8083" }
	srv := &http.Server{ Addr: addr, Handler: r, ReadTimeout: 15*time.Second, WriteTimeout: 60*time.Second }
	srv.ListenAndServe()
}
