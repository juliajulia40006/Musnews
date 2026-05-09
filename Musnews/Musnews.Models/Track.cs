using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Musnews.Models
{
    public class Track
    {
        [Key]
        public int Id { get; set; }

        [Required]
        public string Title { get; set; } = string.Empty;

        public string Artist { get; set; } = string.Empty;

        public string? Album { get; set; }

        public int DurationSec { get; set; }

        public string? AudioUrl { get; set; }

        public int UserId { get; set; }

        [ForeignKey("UserId")]
        public User? User { get; set; }
    }
}