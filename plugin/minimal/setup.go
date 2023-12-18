package minimal

import (
	"github.com/coredns/caddy"
	"ohmydns/core/dnsserver"
	"ohmydns/plugin"
)

func init() {
	plugin.Register("minimal", setup)
}

func setup(c *caddy.Controller) error {
	c.Next()
	if c.NextArg() {
		return plugin.Error("minimal", c.ArgErr())
	}

	dnsserver.GetConfig(c).AddPlugin(func(next plugin.Handler) plugin.Handler {
		return &minimalHandler{Next: next}
	})

	return nil
}
