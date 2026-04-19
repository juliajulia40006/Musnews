namespace Musnews.Models
{
    public class Track
    {
        public int Id { get; set; }
        public string Title { get; set; } = string.Empty;
        public string Artist { get; set; } = string.Empty;
        public string Album { get; set; } = string.Empty;
        public int DurationSec { get; set; }
        public string AudioUrl { get; set; } = string.Empty;
        public string CoverUrl { get; set; } = string.Empty;

    }
}
