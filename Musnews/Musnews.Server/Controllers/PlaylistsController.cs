using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Musnews.Data;
using Musnews.Models;

namespace Musnews.Server.Controllers;

[ApiController]
[Route("api/[controller]")]
public class PlaylistsController : ControllerBase
{
    private readonly AppDbContext _context;

    public PlaylistsController(AppDbContext context)
    {
        _context = context;
    }

    [HttpGet]
    public async Task<ActionResult<IEnumerable<Playlist>>> GetAll()
    {
        var playlists = await _context.Playlists
            .Include(p => p.Tracks)
            .ToListAsync();
        return Ok(playlists);
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<Playlist>> GetById(int id)
    {
        var playlist = await _context.Playlists
            .Include(p => p.Tracks)
            .FirstOrDefaultAsync(p => p.Id == id);

        if (playlist == null)
            return NotFound();

        return Ok(playlist);
    }

    [HttpPost]
    public async Task<ActionResult<Playlist>> Create([FromBody] Playlist playlist)
    {
        _context.Playlists.Add(playlist);
        await _context.SaveChangesAsync();

        return CreatedAtAction(nameof(GetById), new { id = playlist.Id }, playlist);
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> Update(int id, [FromBody] Playlist playlist)
    {
        if (id != playlist.Id)
            return BadRequest("ID in URL does not match ID in body");

        var existingPlaylist = await _context.Playlists.FindAsync(id);
        if (existingPlaylist == null)
            return NotFound();

        existingPlaylist.Name = playlist.Name;

        await _context.SaveChangesAsync();
        return NoContent();
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(int id)
    {
        var playlist = await _context.Playlists.FindAsync(id);
        if (playlist == null)
            return NotFound();

        _context.Playlists.Remove(playlist);
        await _context.SaveChangesAsync();

        return NoContent();
    }

    [HttpPost("{playlistId}/tracks/{trackId}")]
    public async Task<IActionResult> AddTrackToPlaylist(int playlistId, int trackId)
    {
        var playlist = await _context.Playlists
            .Include(p => p.Tracks)
            .FirstOrDefaultAsync(p => p.Id == playlistId);

        if (playlist == null)
            return NotFound("Playlist not found");

        var track = await _context.Tracks.FindAsync(trackId);
        if (track == null)
            return NotFound("Track not found");

        if (playlist.Tracks.Any(t => t.Id == trackId))
            return BadRequest("Track already in playlist");

        playlist.Tracks.Add(track);
        await _context.SaveChangesAsync();

        return NoContent();
    }

    [HttpDelete("{playlistId}/tracks/{trackId}")]
    public async Task<IActionResult> RemoveTrackFromPlaylist(int playlistId, int trackId)
    {
        var playlist = await _context.Playlists
            .Include(p => p.Tracks)
            .FirstOrDefaultAsync(p => p.Id == playlistId);

        if (playlist == null)
            return NotFound("Playlist not found");

        var track = playlist.Tracks.FirstOrDefault(t => t.Id == trackId);
        if (track == null)
            return NotFound("Track not found in playlist");

        playlist.Tracks.Remove(track);
        await _context.SaveChangesAsync();

        return NoContent();
    }
}