"""
Response utility module for standardized API responses
Provides consistent response format across all endpoints with HATEOAS links
"""
from typing import Dict, Any, List, Optional
from flask import request, url_for


class ResponseWrapper:
    """Utility for creating standardized API responses"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", status_code: int = 200, 
                links: Optional[Dict[str, str]] = None) -> tuple:
        """
        Create a successful response
        
        Args:
            data: Response payload
            message: Success message
            status_code: HTTP status code
            links: HATEOAS links to related resources
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        response = {
            "status": "success",
            "message": message,
            "data": data
        }
        if links:
            response["_links"] = links
        return response, status_code
    
    @staticmethod
    def error(error_code: str, message: str, status_code: int = 400, 
              details: Optional[Dict] = None, links: Optional[Dict[str, str]] = None) -> tuple:
        """
        Create an error response
        
        Args:
            error_code: Machine-readable error code
            message: Human-readable error message
            status_code: HTTP status code
            details: Additional error details
            links: HATEOAS links to related resources
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        response = {
            "status": "error",
            "error_code": error_code,
            "message": message
        }
        if details:
            response["details"] = details
        if links:
            response["_links"] = links
        return response, status_code
    
    @staticmethod
    def paginated(items: List[Dict], total: int, limit: int, cursor: Optional[str] = None,
                  next_cursor: Optional[str] = None, links: Optional[Dict[str, str]] = None) -> tuple:
        """
        Create a paginated response
        
        Args:
            items: List of items
            total: Total number of items
            limit: Items per page
            cursor: Current cursor
            next_cursor: Next page cursor
            links: HATEOAS links
            
        Returns:
            Tuple of (response_dict, 200)
        """
        response = {
            "status": "success",
            "data": items,
            "pagination": {
                "total": total,
                "limit": limit,
                "cursor": cursor,
                "next_cursor": next_cursor,
                "has_more": next_cursor is not None
            }
        }
        if links:
            response["_links"] = links
        return response, 200
    
    @staticmethod
    def add_hateoas_links(resource_type: str, resource_id: str = None, 
                         related: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Generate HATEOAS links for a resource
        
        Args:
            resource_type: Type of resource (e.g., 'node', 'session')
            resource_id: ID of the resource
            related: List of related resource types to link to
            
        Returns:
            Dictionary of links
        """
        links = {
            "self": f"/api/v1/{resource_type}s" + (f"/{resource_id}" if resource_id else "")
        }
        
        if related:
            for rel_type in related:
                if resource_id:
                    links[rel_type] = f"/api/v1/{resource_type}s/{resource_id}/{rel_type}"
                else:
                    links[rel_type] = f"/api/v1/{rel_type}s"
        
        return links
