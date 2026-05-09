namespace Musnews.Models.DTO
{
    public class TrackDto
    {
        public int Id { get; set; }
        public string Title { get; set; } = string.Empty;
        public string Artist { get; set; } = string.Empty;
        public string? Album { get; set; }
        public int DurationSec { get; set; }
        public string? AudioUrl { get; set; }
        public int UserId { get; set; }
    }
}